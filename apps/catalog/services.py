"""
Catalog Domain Context - Services

Business logic for asset management and investment operations.
Implements pessimistic locking for concurrent share purchases.
"""

from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from django.db import transaction

from apps.catalog.models import Asset, AssetInventory, AssetPriceHistory
from apps.ledger.services import LedgerService, InsufficientFundsError, LedgerError
from apps.ledger.models import LedgerAccount, AccountCategory
from apps.users.models import UserPosition
from shared.abac.engine import PolicyEngine, AccessContext

if TYPE_CHECKING:
    from apps.users.models import User, Tenant


class CatalogError(Exception):
    """Base exception for catalog operations."""
    pass


class InsufficientSharesError(CatalogError):
    """Raised when not enough shares are available."""
    pass


class PolicyViolationError(CatalogError):
    """Raised when ABAC policy check fails."""
    pass


class CatalogService:
    """Service for asset and inventory management."""

    @staticmethod
    @transaction.atomic
    def create_asset(
        *,
        tenant: 'Tenant',
        name: str,
        symbol: str,
        asset_type: str,
        valuation: Decimal,
        total_shares: Decimal,
        risk_level: int = 3,
        accreditation_required: bool = False,
        minimum_investment: Decimal = Decimal('10.00'),
        description: str = '',
        image_url: str = '',
    ) -> Asset:
        """
        Create a new asset with inventory and escrow account.
        """
        asset = Asset.objects.create(
            tenant=tenant,
            name=name,
            symbol=symbol,
            asset_type=asset_type,
            valuation=valuation,
            total_shares=total_shares,
            risk_level=risk_level,
            accreditation_required=accreditation_required,
            minimum_investment=minimum_investment,
            description=description,
            image_url=image_url,
        )

        # Create inventory with all shares available
        AssetInventory.objects.create(
            asset=asset,
            available_shares=total_shares,
            sold_shares=Decimal('0'),
            reserved_shares=Decimal('0'),
        )

        # Create escrow account for this asset
        LedgerService.create_asset_escrow(
            tenant=tenant,
            asset_symbol=symbol
        )

        return asset

    @staticmethod
    @transaction.atomic
    def reserve_shares(
        *,
        asset: Asset,
        shares: Decimal,
    ) -> AssetInventory:
        """
        Reserve shares for a pending purchase.
        
        Uses pessimistic locking (select_for_update) to prevent
        overselling under concurrent load.
        """
        # Lock the inventory row
        inventory = AssetInventory.objects.select_for_update().get(asset=asset)

        if not inventory.can_reserve(shares):
            raise InsufficientSharesError(
                f"Cannot reserve {shares} shares. Only {inventory.available_shares} available."
            )

        inventory.available_shares -= shares
        inventory.reserved_shares += shares
        inventory.save(update_fields=['available_shares', 'reserved_shares', 'updated_at'])

        return inventory

    @staticmethod
    @transaction.atomic
    def release_reserved_shares(
        *,
        asset: Asset,
        shares: Decimal,
    ) -> AssetInventory:
        """
        Release reserved shares back to available (rollback).
        """
        inventory = AssetInventory.objects.select_for_update().get(asset=asset)

        inventory.reserved_shares -= shares
        inventory.available_shares += shares
        inventory.save(update_fields=['available_shares', 'reserved_shares', 'updated_at'])

        return inventory

    @staticmethod
    @transaction.atomic
    def complete_purchase(
        *,
        asset: Asset,
        shares: Decimal,
    ) -> AssetInventory:
        """
        Complete a purchase by moving reserved shares to sold.
        """
        inventory = AssetInventory.objects.select_for_update().get(asset=asset)

        inventory.reserved_shares -= shares
        inventory.sold_shares += shares
        inventory.save(update_fields=['reserved_shares', 'sold_shares', 'updated_at'])

        return inventory


class InvestService:
    """
    The main investment transaction script.
    
    Coordinates between Ledger, Catalog, and User domains
    to execute a share purchase atomically.
    """

    def __init__(self, policy_engine: Optional[PolicyEngine] = None):
        self.policy_engine = policy_engine or PolicyEngine()

    @transaction.atomic
    def invest(
        self,
        *,
        user: 'User',
        asset: Asset,
        shares: Decimal,
    ) -> dict:
        """
        Execute an investment transaction.
        
        Steps:
        1. Check ABAC policies
        2. Calculate total cost
        3. Reserve shares (with lock)
        4. Transfer funds from wallet to escrow
        5. Complete purchase
        6. Update user position
        
        Returns transaction details on success.
        """
        # Step 1: Check ABAC policies
        context = AccessContext(user=user, resource=asset)
        policy_result = self.policy_engine.check_all(context)
        
        if not policy_result.allowed:
            raise PolicyViolationError(
                f"Access denied: {', '.join(policy_result.violations)}"
            )

        # Step 2: Calculate cost
        total_cost = shares * asset.valuation

        if total_cost < asset.minimum_investment:
            raise CatalogError(
                f"Minimum investment is {asset.minimum_investment}. "
                f"Your order: {total_cost}"
            )

        # Step 3: Reserve shares (pessimistic lock)
        try:
            CatalogService.reserve_shares(asset=asset, shares=shares)
        except InsufficientSharesError:
            raise

        # Step 4: Transfer funds
        try:
            wallet = LedgerService.get_user_wallet(user)
            if not wallet:
                raise LedgerError(f"No wallet found for user {user.username}")

            escrow = LedgerAccount.objects.get(
                tenant=user.tenant,
                category=AccountCategory.ASSET_ESCROW,
                name__contains=asset.symbol
            )

            entry = LedgerService.transfer(
                from_account=wallet,
                to_account=escrow,
                amount=total_cost,
                description=f"Investment: {shares} shares of {asset.symbol}",
                entry_type='INVESTMENT',
                created_by=user
            )

        except (InsufficientFundsError, LedgerError) as e:
            # Rollback: release reserved shares
            CatalogService.release_reserved_shares(asset=asset, shares=shares)
            raise

        # Step 5: Complete purchase
        CatalogService.complete_purchase(asset=asset, shares=shares)

        # Step 6: Update user position
        position, created = UserPosition.objects.get_or_create(
            user=user,
            asset=asset,
            defaults={'shares': Decimal('0'), 'average_cost': Decimal('0')}
        )

        # Calculate new average cost
        old_total_cost = position.shares * position.average_cost
        new_total_cost = old_total_cost + total_cost
        new_total_shares = position.shares + shares

        position.shares = new_total_shares
        position.average_cost = new_total_cost / new_total_shares if new_total_shares > 0 else Decimal('0')
        position.save(update_fields=['shares', 'average_cost', 'updated_at'])

        return {
            'new_position': str(position.shares),
        }

    @transaction.atomic
    def sell(
        self,
        *,
        user: 'User',
        asset: Asset,
        shares: Decimal,
    ) -> dict:
        """
        Execute a divestment (sell) transaction.
        
        Steps:
        1. Check user position
        2. Calculate total value
        3. Transfer funds from escrow to wallet
        4. Update inventory (Available += shares)
        5. Update user position
        """
        # Step 1: Check position
        try:
            position = UserPosition.objects.select_for_update().get(user=user, asset=asset)
            if position.shares < shares:
                raise InsufficientSharesError(f"Insufficient shares. You own {position.shares}.")
        except UserPosition.DoesNotExist:
            raise InsufficientSharesError("You do not own any shares of this asset.")

        # Step 2: Calculate value
        total_value = shares * asset.valuation

        # Step 3: Transfer funds (Escrow -> Wallet)
        wallet = LedgerService.get_user_wallet(user)
        escrow = LedgerAccount.objects.get(
            tenant=user.tenant,
            category=AccountCategory.ASSET_ESCROW,
            name__contains=asset.symbol
        )

        entry = LedgerService.transfer(
            from_account=escrow,
            to_account=wallet,
            amount=total_value,
            description=f"Divestment: {shares} shares of {asset.symbol}",
            entry_type='DIVESTMENT',
            created_by=user
        )

        # Step 4: Update Inventory
        inventory = AssetInventory.objects.select_for_update().get(asset=asset)
        inventory.sold_shares -= shares
        inventory.available_shares += shares
        inventory.save(update_fields=['sold_shares', 'available_shares', 'updated_at'])

        # Step 5: Update User Position
        position.shares -= shares
        position.save(update_fields=['shares', 'updated_at'])

        return {
            'success': True,
            'reference': entry.reference,
            'asset': asset.symbol,
            'shares_sold': str(shares),
            'price_per_share': str(asset.valuation),
            'total_value': str(total_value),
            'remaining_position': str(position.shares),
        }
