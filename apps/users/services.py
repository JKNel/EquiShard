"""
Users Domain Context - Services

Business logic for user management and authentication.
"""

from typing import Optional

from django.db import transaction

from apps.users.models import Tenant, User
from apps.ledger.services import LedgerService


class UserService:
    """Service for user-related business operations."""

    @staticmethod
    @transaction.atomic
    def create_user(
        *,
        username: str,
        email: str,
        password: str,
        tenant: Tenant,
        first_name: str = '',
        last_name: str = '',
        risk_tolerance: int = 3,
        is_accredited: bool = False,
    ) -> User:
        """
        Create a new user with associated wallet account.
        
        This creates both the User and their LedgerAccount (wallet)
        in a single transaction.
        """
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            tenant=tenant,
            first_name=first_name,
            last_name=last_name,
            risk_tolerance=risk_tolerance,
            is_accredited=is_accredited,
        )
        
        # Create user's wallet account in the ledger
        LedgerService.create_user_wallet(user=user, tenant=tenant)
        
        return user

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            return User.objects.select_related('tenant').get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def update_risk_profile(
        user: User,
        *,
        risk_tolerance: Optional[int] = None,
        is_accredited: Optional[bool] = None,
    ) -> User:
        """Update user's ABAC attributes."""
        if risk_tolerance is not None:
            user.risk_tolerance = max(1, min(5, risk_tolerance))
        if is_accredited is not None:
            user.is_accredited = is_accredited
        user.save(update_fields=['risk_tolerance', 'is_accredited', 'updated_at'])
        return user


class TenantService:
    """Service for tenant management."""

    @staticmethod
    @transaction.atomic
    def create_tenant(*, name: str, slug: str) -> Tenant:
        """
        Create a new tenant with system accounts.
        
        Creates the tenant and their system reserve account
        for the double-entry ledger.
        """
        tenant = Tenant.objects.create(name=name, slug=slug)
        
        # Create system reserve account for this tenant
        LedgerService.create_system_reserve(tenant=tenant)
        
        return tenant

    @staticmethod
    def get_tenant_by_slug(slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        try:
            return Tenant.objects.get(slug=slug, is_active=True)
        except Tenant.DoesNotExist:
            return None
