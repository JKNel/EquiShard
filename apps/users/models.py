"""
Users Domain Context - Models

Handles identity, tenancy, and user attributes for ABAC.
"""

from decimal import Decimal
from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.db import models


class Tenant(models.Model):
    """
    Multi-tenant organization entity.
    
    All domain entities are scoped to a tenant for isolation.
    """
    name: str = models.CharField(max_length=255)
    slug: str = models.SlugField(max_length=100, unique=True)
    is_active: bool = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenants'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """
    Custom User model with tenant association and ABAC attributes.
    
    Attributes:
        tenant: The organization this user belongs to
        risk_tolerance: Risk level the user is comfortable with (1-5)
        is_accredited: Whether user is an accredited investor
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name='users',
        null=True,
        blank=True,
    )
    
    # ABAC Attributes
    risk_tolerance: int = models.IntegerField(
        default=3,
        help_text="Risk tolerance level (1=Low, 5=High)"
    )
    is_accredited: bool = models.BooleanField(
        default=False,
        help_text="Whether user is an accredited investor"
    )
    
    # Profile
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def __str__(self) -> str:
        return f"{self.email} ({self.tenant.slug if self.tenant else 'no-tenant'})"

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username


class UserPosition(models.Model):
    """
    Tracks user's ownership positions in assets.
    
    This is a read-optimized denormalization of ledger data
    for quick portfolio queries.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='positions'
    )
    asset = models.ForeignKey(
        'catalog.Asset',
        on_delete=models.PROTECT,
        related_name='holder_positions'
    )
    shares: Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0')
    )
    average_cost: Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_positions'
        unique_together = [['user', 'asset']]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.asset.symbol}: {self.shares}"

    @property
    def current_value(self) -> Decimal:
        """Calculate current position value based on asset valuation."""
        return self.shares * self.asset.valuation
