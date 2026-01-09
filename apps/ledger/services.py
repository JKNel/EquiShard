"""
Ledger Domain Context - Services

Business logic for double-entry accounting operations.
All money movement happens through these services.
"""

from decimal import Decimal
from typing import Optional, TYPE_CHECKING
import uuid

from django.db import transaction
from django.utils import timezone

from apps.ledger.models import (
    LedgerAccount,
    JournalEntry,
    TransactionLine,
    AccountType,
    AccountCategory,
)

if TYPE_CHECKING:
    from apps.users.models import User, Tenant


class LedgerError(Exception):
    """Base exception for ledger operations."""
    pass


class InsufficientFundsError(LedgerError):
    """Raised when an account doesn't have enough balance."""
    pass


class LedgerService:
    """
    Service for ledger operations.
    
    All operations that move money must go through this service
    to maintain double-entry integrity.
    """

    @staticmethod
    @transaction.atomic
    def create_user_wallet(*, user: 'User', tenant: 'Tenant') -> LedgerAccount:
        """Create a wallet account for a user."""
        return LedgerAccount.objects.create(
            tenant=tenant,
            owner=user,
            account_type=AccountType.ASSET,
            category=AccountCategory.USER_WALLET,
            currency='USD',
            name=f"Wallet - {user.username}",
            description=f"Primary wallet for user {user.email}"
        )

    @staticmethod
    @transaction.atomic
    def create_system_reserve(*, tenant: 'Tenant') -> LedgerAccount:
        """Create the system reserve account for a tenant."""
        return LedgerAccount.objects.create(
            tenant=tenant,
            owner=None,  # System account
            account_type=AccountType.LIABILITY,
            category=AccountCategory.SYSTEM_RESERVE,
            currency='USD',
            name=f"System Reserve - {tenant.slug}",
            description="System reserve for faucet operations"
        )

    @staticmethod
    @transaction.atomic
    def create_asset_escrow(
        *,
        tenant: 'Tenant',
        asset_symbol: str
    ) -> LedgerAccount:
        """Create an escrow account for asset purchases."""
        return LedgerAccount.objects.create(
            tenant=tenant,
            owner=None,
            account_type=AccountType.LIABILITY,
            category=AccountCategory.ASSET_ESCROW,
            currency='USD',
            name=f"Escrow - {asset_symbol}",
            description=f"Escrow account for {asset_symbol} purchases"
        )

    @staticmethod
    def get_user_wallet(user: 'User') -> Optional[LedgerAccount]:
        """Get the user's primary wallet account."""
        try:
            return LedgerAccount.objects.get(
                owner=user,
                category=AccountCategory.USER_WALLET,
                is_active=True
            )
        except LedgerAccount.DoesNotExist:
            return None

    @staticmethod
    def get_system_reserve(tenant: 'Tenant') -> Optional[LedgerAccount]:
        """Get the tenant's system reserve account."""
        try:
            return LedgerAccount.objects.get(
                tenant=tenant,
                category=AccountCategory.SYSTEM_RESERVE,
                is_active=True
            )
        except LedgerAccount.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def faucet(
        *,
        user: 'User',
        amount: Decimal,
        description: str = "Faucet credit"
    ) -> JournalEntry:
        """
        Add funds to a user's wallet from the system reserve.
        
        This is the ONLY way to create money in the system.
        
        Double-entry:
        - DR (debit) User Wallet (Asset increases)
        - CR (credit) System Reserve (Liability increases)
        """
        if amount <= 0:
            raise LedgerError("Faucet amount must be positive")

        wallet = LedgerService.get_user_wallet(user)
        if not wallet:
            raise LedgerError(f"No wallet found for user {user.username}")

        reserve = LedgerService.get_system_reserve(user.tenant)
        if not reserve:
            raise LedgerError(f"No system reserve for tenant {user.tenant.slug}")

        # Create journal entry
        entry = JournalEntry.objects.create(
            reference=f"FAUCET-{uuid.uuid4().hex[:12].upper()}",
            description=description,
            entry_type='FAUCET',
            created_by=user
        )

        # Debit user wallet (increase asset)
        wallet_balance = wallet.get_balance() + amount
        TransactionLine.objects.create(
            journal_entry=entry,
            account=wallet,
            amount=amount,  # Positive = Debit
            balance_snapshot=wallet_balance,
            memo=f"Faucet credit: {description}"
        )

        # Credit system reserve (increase liability)
        reserve_balance = reserve.get_balance() - amount
        TransactionLine.objects.create(
            journal_entry=entry,
            account=reserve,
            amount=-amount,  # Negative = Credit
            balance_snapshot=reserve_balance,
            memo=f"Faucet credit to {user.username}"
        )

        # Post the entry
        entry.post()

        return entry

    @staticmethod
    @transaction.atomic
    def transfer(
        *,
        from_account: LedgerAccount,
        to_account: LedgerAccount,
        amount: Decimal,
        description: str,
        entry_type: str = 'TRANSFER',
        created_by: Optional['User'] = None
    ) -> JournalEntry:
        """
        Transfer funds between accounts.
        
        Double-entry:
        - DR to_account (increase)
        - CR from_account (decrease)
        """
        if amount <= 0:
            raise LedgerError("Transfer amount must be positive")

        # Check sufficient funds for asset accounts
        if from_account.account_type == AccountType.ASSET:
            current_balance = from_account.get_balance()
            if current_balance < amount:
                raise InsufficientFundsError(
                    f"Insufficient funds: {current_balance} < {amount}"
                )

        # Create journal entry
        entry = JournalEntry.objects.create(
            reference=f"{entry_type}-{uuid.uuid4().hex[:12].upper()}",
            description=description,
            entry_type=entry_type,
            created_by=created_by
        )

        # Debit to_account (increase)
        to_balance = to_account.get_balance() + amount
        TransactionLine.objects.create(
            journal_entry=entry,
            account=to_account,
            amount=amount,
            balance_snapshot=to_balance,
            memo=f"Received from {from_account.name}"
        )

        # Credit from_account (decrease)
        from_balance = from_account.get_balance() - amount
        TransactionLine.objects.create(
            journal_entry=entry,
            account=from_account,
            amount=-amount,
            balance_snapshot=from_balance,
            memo=f"Sent to {to_account.name}"
        )

        entry.post()

        return entry

    @staticmethod
    def get_balance(user: 'User') -> Decimal:
        """Get user's wallet balance."""
        wallet = LedgerService.get_user_wallet(user)
        return wallet.get_balance() if wallet else Decimal('0')

    @staticmethod
    def get_transaction_history(
        user: 'User',
        limit: int = 50
    ) -> list[TransactionLine]:
        """Get user's transaction history."""
        wallet = LedgerService.get_user_wallet(user)
        if not wallet:
            return []

        return list(
            TransactionLine.objects.filter(
                account=wallet,
                journal_entry__posted=True
            ).select_related('journal_entry').order_by('-created_at')[:limit]
        )
