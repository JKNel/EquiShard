"""Users app admin configuration."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import Tenant, User, UserPosition


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'tenant', 'risk_tolerance', 'is_accredited', 'is_active']
    list_filter = ['tenant', 'is_accredited', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Tenant & ABAC', {'fields': ('tenant', 'risk_tolerance', 'is_accredited')}),
        ('Profile', {'fields': ('phone', 'date_of_birth')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Tenant & ABAC', {'fields': ('tenant', 'risk_tolerance', 'is_accredited')}),
    )


@admin.register(UserPosition)
class UserPositionAdmin(admin.ModelAdmin):
    list_display = ['user', 'asset', 'shares', 'average_cost', 'current_value']
    list_filter = ['asset']
    search_fields = ['user__username', 'asset__symbol']
    raw_id_fields = ['user', 'asset']
