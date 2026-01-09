"""
Ledger Domain Context - Models

Double-entry accounting system for tracking all money movement.
No "magic balances" - money is only moved, never created/destroyed.
"""

from decimal import Decimal
from typing import Optional
import uuid

from django.db import models
from django.core.exceptions import ValidationError


class AccountType(models.TextChoices):
    """Account types following double-entry accounting."""
    ASSET = 'ASSET', 'Asset'  # Increases with debits (positive amounts)
    LIABILITY = 'LIABILITY', 'Liability'  # Increases with credits (negative amounts)
    EQUITY = 'EQUITY', 'Equity'
    REVENUE = 'REVENUE', 'Revenue'
    EXPENSE = 'EXPENSE', 'Expense'


class AccountCategory(models.TextChoices):
    """Categories for different account purposes."""
    USER_WALLET = 'USER_WALLET', 'User Wallet'
    SYSTEM_RESERVE = 'SYSTEM_RESERVE', 'System Reserve'
    ASSET_ESCROW = 'ASSET_ESCROW', 'Asset Escrow'
    FEE_COLLECTION = 'FEE_COLLECTION', 'Fee Collection'


class LedgerAccount(models.Model):
    """
    A bucket for holding value (e.g., User Wallet, Asset Escrow).
    
    Each account belongs to a tenant and optionally to a user.
    """
    tenant = models.ForeignKey(
        'users.Tenant',
        on_delete=models.PROTECT,
        related_name='ledger_accounts'
    )
    owner = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='ledger_accounts',
        null=True,
        blank=True,
        help_text="Null for system accounts"
    )
    
    account_type: str = models.CharField(
        max_length=20,
        choices=AccountType.choices
    )
    category: str = models.CharField(
        max_length=30,
        choices=AccountCategory.choices
    )
    currency: str = models.CharField(max_length=3, default='USD')
    
    name: str = models.CharField(max_length=255)
    description: str = models.TextField(blank=True)
    
    is_active: bool = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ledger_accounts'
        indexes = [
            models.Index(fields=['tenant', 'category']),
            models.Index(fields=['owner', 'category']),
        ]

    def __str__(self) -> str:
        owner_str = self.owner.username if self.owner else 'SYSTEM'
        return f"{self.name} ({owner_str}) - {self.currency}"

    def get_balance(self) -> Decimal:
        """
        Calculate current balance from transaction lines.
        
        For ASSET accounts: positive balance means we own something
        For LIABILITY accounts: positive balance means we owe something
        """
        from django.db.models import Sum
        
        result = self.transaction_lines.filter(
            journal_entry__posted=True
        ).aggregate(total=Sum('amount'))
        
        return result['total'] or Decimal('0')


class JournalEntry(models.Model):
    """
    An atomic accounting event - the container for balanced transactions.
    
    Every JournalEntry must have TransactionLines that sum to zero.
    """
    reference: str = models.CharField(
        max_length=100,
        unique=True,
        default=uuid.uuid4,
        help_text="Unique transaction reference"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    posted: bool = models.BooleanField(
        default=False,
        help_text="Whether this entry is finalized"
    )
    
    description: str = models.CharField(max_length=500)
    entry_type: str = models.CharField(
        max_length=50,
        help_text="Type of entry (FAUCET, INVESTMENT, TRANSFER, etc.)"
    )
    
    # Metadata for audit trail
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='journal_entries',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'journal_entries'
        ordering = ['-timestamp']
        verbose_name_plural = 'Journal entries'

    def __str__(self) -> str:
        status = '✓' if self.posted else '○'
        return f"{status} {self.reference} - {self.description[:50]}"

    def clean(self) -> None:
        """Validate that transaction lines sum to zero."""
        if self.pk:  # Only validate on update
            total = self.lines.aggregate(total=models.Sum('amount'))['total']
            if total and total != Decimal('0'):
                raise ValidationError(
                    f"Transaction lines must sum to zero. Current sum: {total}"
                )

    def post(self) -> None:
        """Finalize the journal entry after validation."""
        self.clean()
        self.posted = True
        self.save(update_fields=['posted'])


class TransactionLine(models.Model):
    """
    A single debit or credit line in a journal entry.
    
    Amount conventions:
    - Positive = Debit (increases assets, decreases liabilities)
    - Negative = Credit (decreases assets, increases liabilities)
    """
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    account = models.ForeignKey(
        LedgerAccount,
        on_delete=models.PROTECT,
        related_name='transaction_lines'
    )
    
    amount: Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Positive=Debit, Negative=Credit"
    )
    balance_snapshot: Decimal = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        help_text="Account balance after this transaction"
    )
    
    memo: str = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transaction_lines'
        ordering = ['journal_entry', 'id']

    def __str__(self) -> str:
        direction = 'DR' if self.amount > 0 else 'CR'
        return f"{direction} {abs(self.amount)} -> {self.account.name}"
