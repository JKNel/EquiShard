"""
Catalog Domain Context - Models

Asset management with static metadata and volatile inventory.
Separates data to prevent locking issues during high-concurrency purchases.
"""

from decimal import Decimal
from typing import Optional

from django.db import models


class AssetType(models.TextChoices):
    """Asset categories for portfolio allocation."""
    REAL_ESTATE = 'REAL_ESTATE', 'Real Estate'
    TECH_STOCKS = 'TECH_STOCKS', 'Tech Stocks'
    COMMODITIES = 'COMMODITIES', 'Commodities'
    BONDS = 'BONDS', 'Bonds'
    CRYPTO = 'CRYPTO', 'Cryptocurrency'
    PRIVATE_EQUITY = 'PRIVATE_EQUITY', 'Private Equity'
    ART = 'ART', 'Art & Collectibles'


class Asset(models.Model):
    """
    Static asset metadata.
    
    This data rarely changes and doesn't need locking during purchases.
    """
    tenant = models.ForeignKey(
        'users.Tenant',
        on_delete=models.PROTECT,
        related_name='assets'
    )
    
    # Basic info
    name: str = models.CharField(max_length=255)
    symbol: str = models.CharField(max_length=20)
    description: str = models.TextField(blank=True)
    
    # Classification
    asset_type: str = models.CharField(
        max_length=30,
        choices=AssetType.choices
    )
    
    # Valuation
    valuation: Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Current price per share"
    )
    total_shares: Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Total shares available for this asset"
    )
    
    # ABAC attributes
    risk_level: int = models.IntegerField(
        default=3,
        help_text="Risk level (1=Low, 5=High)"
    )
    accreditation_required: bool = models.BooleanField(
        default=False,
        help_text="Requires accredited investor status"
    )
    minimum_investment: Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('10.00')
    )
    
    # Media
    image_url: str = models.URLField(blank=True)
    
    # Status
    is_active: bool = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assets'
        unique_together = [['tenant', 'symbol']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'asset_type']),
            models.Index(fields=['risk_level']),
        ]

    def __str__(self) -> str:
        return f"{self.symbol} - {self.name}"

    @property
    def market_cap(self) -> Decimal:
        """Total market capitalization."""
        return self.valuation * self.total_shares


class AssetInventory(models.Model):
    """
    Volatile inventory data for an asset.
    
    This is the ONLY model that should be locked during purchase operations.
    Uses select_for_update() for pessimistic locking.
    """
    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    
    available_shares: Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0'),
        help_text="Shares available for purchase"
    )
    sold_shares: Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0'),
        help_text="Shares that have been sold"
    )
    reserved_shares: Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0'),
        help_text="Shares reserved for pending transactions"
    )
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asset_inventory'
        verbose_name_plural = 'Asset inventories'

    def __str__(self) -> str:
        return f"Inventory: {self.asset.symbol}"

    @property
    def total_allocated(self) -> Decimal:
        """Total shares that are sold or reserved."""
        return self.sold_shares + self.reserved_shares

    def can_reserve(self, shares: Decimal) -> bool:
        """Check if the requested shares can be reserved."""
        return self.available_shares >= shares


class AssetPriceHistory(models.Model):
    """
    Historical price data for charts and analytics.
    
    Populated by the seeding script and updated by price feeds.
    """
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    
    price: Decimal = models.DecimalField(max_digits=20, decimal_places=8)
    volume: Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0')
    )
    
    recorded_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'asset_price_history'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['asset', 'recorded_at']),
        ]

    def __str__(self) -> str:
        return f"{self.asset.symbol} @ {self.price} ({self.recorded_at})"
