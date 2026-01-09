"""Ledger app admin configuration."""

from django.contrib import admin

from apps.ledger.models import LedgerAccount, JournalEntry, TransactionLine


class TransactionLineInline(admin.TabularInline):
    model = TransactionLine
    extra = 0
    readonly_fields = ['amount', 'balance_snapshot', 'account', 'memo', 'created_at']
    can_delete = False


@admin.register(LedgerAccount)
class LedgerAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'tenant', 'account_type', 'category', 'currency', 'get_balance', 'is_active']
    list_filter = ['account_type', 'category', 'currency', 'tenant', 'is_active']
    search_fields = ['name', 'owner__username', 'tenant__name']
    raw_id_fields = ['owner']

    def get_balance(self, obj):
        return f"{obj.get_balance():,.2f}"
    get_balance.short_description = 'Balance'


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['reference', 'entry_type', 'description', 'posted', 'created_by', 'timestamp']
    list_filter = ['posted', 'entry_type', 'timestamp']
    search_fields = ['reference', 'description']
    readonly_fields = ['reference', 'timestamp', 'created_at']
    inlines = [TransactionLineInline]

    def has_change_permission(self, request, obj=None):
        # Don't allow editing posted entries
        if obj and obj.posted:
            return False
        return super().has_change_permission(request, obj)


@admin.register(TransactionLine)
class TransactionLineAdmin(admin.ModelAdmin):
    list_display = ['journal_entry', 'account', 'amount', 'balance_snapshot', 'created_at']
    list_filter = ['account__category', 'journal_entry__entry_type']
    search_fields = ['journal_entry__reference', 'account__name', 'memo']
    raw_id_fields = ['journal_entry', 'account']
    readonly_fields = ['created_at']
