"""Catalog app admin configuration."""

from django.contrib import admin

from apps.catalog.models import Asset, AssetInventory, AssetPriceHistory


class AssetInventoryInline(admin.StackedInline):
    model = AssetInventory
    can_delete = False
    readonly_fields = ['available_shares', 'sold_shares', 'reserved_shares']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = [
        'symbol', 'name', 'asset_type', 'valuation', 'risk_level',
        'accreditation_required', 'is_active', 'tenant'
    ]
    list_filter = ['asset_type', 'risk_level', 'accreditation_required', 'tenant', 'is_active']
    search_fields = ['name', 'symbol', 'description']
    inlines = [AssetInventoryInline]


@admin.register(AssetInventory)
class AssetInventoryAdmin(admin.ModelAdmin):
    list_display = ['asset', 'available_shares', 'sold_shares', 'reserved_shares', 'updated_at']
    list_filter = ['asset__tenant']
    search_fields = ['asset__symbol', 'asset__name']
    raw_id_fields = ['asset']
    readonly_fields = ['available_shares', 'sold_shares', 'reserved_shares']


@admin.register(AssetPriceHistory)
class AssetPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['asset', 'price', 'volume', 'recorded_at']
    list_filter = ['asset__tenant', 'recorded_at']
    search_fields = ['asset__symbol']
    raw_id_fields = ['asset']
    date_hierarchy = 'recorded_at'
