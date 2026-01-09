#!/usr/bin/env python
"""
Seed Script for EquiShard

Generates:
- 3 Tenants
- 50 Assets across tenants
- Users per tenant
- 30 days of simulated trading history with price movements
"""

import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'equishard.settings')

import django
django.setup()

from django.db import transaction
from apps.users.models import Tenant, User
from apps.users.services import TenantService, UserService
from apps.ledger.services import LedgerService
from apps.catalog.models import Asset, AssetInventory, AssetPriceHistory, AssetType
from apps.catalog.services import CatalogService


# ============================================================================
# Configuration
# ============================================================================

TENANTS = [
    {"name": "Alpha Investments", "slug": "alpha"},
    {"name": "Beta Capital", "slug": "beta"},
    {"name": "Gamma Holdings", "slug": "gamma"},
]

ASSETS_PER_TENANT = 20  # 20 per tenant = 60 total

# Base path for asset images (relative URL for serving)
IMAGE_BASE_PATH = "/static/assets/images"

ASSET_TEMPLATES = [
    # Real Estate (3 images available)
    {"name": "Urban Tower REIT", "symbol": "UTR", "type": AssetType.REAL_ESTATE, "valuation": "150.00", "risk": 2, "image": f"{IMAGE_BASE_PATH}/real_estate/property 1.jpg"},
    {"name": "Coastal Properties", "symbol": "CPP", "type": AssetType.REAL_ESTATE, "valuation": "85.50", "risk": 3, "image": f"{IMAGE_BASE_PATH}/real_estate/property 2.jpg"},
    {"name": "Industrial Parks Inc", "symbol": "IPI", "type": AssetType.REAL_ESTATE, "valuation": "220.00", "risk": 2, "image": f"{IMAGE_BASE_PATH}/real_estate/property 3.jpg"},
    
    # Tech Stocks (3 images available)
    {"name": "Cloud Dynamics", "symbol": "CLD", "type": AssetType.TECH_STOCKS, "valuation": "1250.00", "risk": 4, "image": f"{IMAGE_BASE_PATH}/tech_stocks/company 1.png"},
    {"name": "AI Innovations", "symbol": "AII", "type": AssetType.TECH_STOCKS, "valuation": "890.00", "risk": 5, "accredited": True, "image": f"{IMAGE_BASE_PATH}/tech_stocks/company 2.jpg"},
    {"name": "Quantum Computing Co", "symbol": "QCC", "type": AssetType.TECH_STOCKS, "valuation": "340.00", "risk": 5, "accredited": True, "image": f"{IMAGE_BASE_PATH}/tech_stocks/company 3.png"},
    {"name": "Cyber Shield Inc", "symbol": "CSI", "type": AssetType.TECH_STOCKS, "valuation": "275.00", "risk": 3, "image": f"{IMAGE_BASE_PATH}/tech_stocks/company 1.png"},
    {"name": "Green Tech Solutions", "symbol": "GTS", "type": AssetType.TECH_STOCKS, "valuation": "180.00", "risk": 3, "image": f"{IMAGE_BASE_PATH}/tech_stocks/company 2.jpg"},
    
    # Commodities (3 images available)
    {"name": "Gold Standard Fund", "symbol": "GSF", "type": AssetType.COMMODITIES, "valuation": "1850.00", "risk": 2, "image": f"{IMAGE_BASE_PATH}/commodities/gold.jpg"},
    {"name": "Silver Stream", "symbol": "SST", "type": AssetType.COMMODITIES, "valuation": "24.50", "risk": 3, "image": f"{IMAGE_BASE_PATH}/commodities/silver.jpg"},
    {"name": "Rare Earth Minerals", "symbol": "REM", "type": AssetType.COMMODITIES, "valuation": "560.00", "risk": 4, "image": f"{IMAGE_BASE_PATH}/commodities/coal pile.png"},
    
    # Private Equity (3 images available)
    {"name": "Venture Growth Fund", "symbol": "VGF", "type": AssetType.PRIVATE_EQUITY, "valuation": "5000.00", "risk": 5, "accredited": True, "image": f"{IMAGE_BASE_PATH}/private_equity/equity firm 1.png"},
    {"name": "Buyout Partners", "symbol": "BOP", "type": AssetType.PRIVATE_EQUITY, "valuation": "2500.00", "risk": 5, "accredited": True, "image": f"{IMAGE_BASE_PATH}/private_equity/equity firm 2.png"},
    {"name": "Growth Capital LP", "symbol": "GCL", "type": AssetType.PRIVATE_EQUITY, "valuation": "3500.00", "risk": 5, "accredited": True, "image": f"{IMAGE_BASE_PATH}/private_equity/equity firm 3.png"},
    
    # Bonds (3 images available)
    {"name": "US Treasury Bond Fund", "symbol": "TBF", "type": AssetType.BONDS, "valuation": "100.00", "risk": 1, "image": f"{IMAGE_BASE_PATH}/bonds/usa bond.jpg"},
    {"name": "UK Gilt Fund", "symbol": "UKG", "type": AssetType.BONDS, "valuation": "95.00", "risk": 1, "image": f"{IMAGE_BASE_PATH}/bonds/uk bond.jpg"},
    {"name": "German Bund ETF", "symbol": "GBE", "type": AssetType.BONDS, "valuation": "98.00", "risk": 1, "image": f"{IMAGE_BASE_PATH}/bonds/germany bond.jpg"},
    
    # Collectibles (3 images available)
    {"name": "Modern Art Collection", "symbol": "MAC", "type": AssetType.ART, "valuation": "15000.00", "risk": 4, "accredited": True, "image": f"{IMAGE_BASE_PATH}/collectibles/collectable 1.jpg"},
    {"name": "Vintage Wine Fund", "symbol": "VWF", "type": AssetType.ART, "valuation": "8500.00", "risk": 4, "accredited": True, "image": f"{IMAGE_BASE_PATH}/collectibles/collectable 2.jpg"},
    {"name": "Classic Cars Portfolio", "symbol": "CCP", "type": AssetType.ART, "valuation": "25000.00", "risk": 5, "accredited": True, "image": f"{IMAGE_BASE_PATH}/collectibles/collectable 3.jpg"},
]

USERS_PER_TENANT = [
    {"username": "investor1", "email": "investor1@{}.com", "risk": 3, "accredited": False, "balance": "10000.00"},
    {"username": "investor2", "email": "investor2@{}.com", "risk": 4, "accredited": False, "balance": "25000.00"},
    {"username": "vip_investor", "email": "vip@{}.com", "risk": 5, "accredited": True, "balance": "100000.00"},
]


# ============================================================================
# Seeding Functions
# ============================================================================

def create_tenants() -> list[Tenant]:
    """Create tenants with system reserve accounts."""
    print("Creating tenants...")
    tenants = []
    
    for tenant_data in TENANTS:
        tenant = TenantService.create_tenant(
            name=tenant_data["name"],
            slug=tenant_data["slug"]
        )
        tenants.append(tenant)
        print(f"  ✓ Created tenant: {tenant.name}")
    
    return tenants


def create_users(tenants: list[Tenant]) -> list[User]:
    """Create users for each tenant."""
    print("\nCreating users...")
    users = []
    
    for tenant in tenants:
        for user_template in USERS_PER_TENANT:
            user = UserService.create_user(
                username=f"{user_template['username']}_{tenant.slug}",
                email=user_template["email"].format(tenant.slug),
                password="password123",
                tenant=tenant,
                first_name=user_template["username"].replace("_", " ").title(),
                last_name=tenant.name.split()[0],
                risk_tolerance=user_template["risk"],
                is_accredited=user_template["accredited"],
            )
            
            # Add initial balance via faucet
            LedgerService.faucet(
                user=user,
                amount=Decimal(user_template["balance"]),
                description="Initial deposit"
            )
            
            users.append(user)
            print(f"  ✓ Created user: {user.username} with ${user_template['balance']}")
    
    return users


def create_admin():
    """Create a superuser for administration."""
    print("\nCheck/Create Admin User...")
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@equishard.com",
            password="password123"
        )
        print("  ✓ Created superuser: admin")
    else:
        print("  ✓ Admin user already exists")


def create_assets(tenants: list[Tenant]) -> list[Asset]:
    """Create assets for each tenant."""
    print("\nCreating assets...")
    assets = []
    
    for tenant in tenants:
        for i, template in enumerate(ASSET_TEMPLATES):
            # Create unique symbol per tenant
            symbol = f"{template['symbol']}-{tenant.slug.upper()[:1]}"
            
            asset = CatalogService.create_asset(
                tenant=tenant,
                name=template["name"],
                symbol=symbol,
                asset_type=template["type"],
                valuation=Decimal(template["valuation"]),
                total_shares=Decimal("100000"),  # 100k shares per asset
                risk_level=template["risk"],
                accreditation_required=template.get("accredited", False),
                minimum_investment=Decimal("10.00"),
                description=f"Fractional shares of {template['name']} - diversified investment opportunity.",
                image_url=template.get("image", ""),
            )
            assets.append(asset)
        
        print(f"  ✓ Created {len(ASSET_TEMPLATES)} assets for {tenant.name}")
    
    return assets


def create_price_history(assets: list[Asset], days: int = 30):
    """Generate simulated price history for charts."""
    print(f"\nGenerating {days} days of price history...")
    
    now = datetime.now()
    history_entries = []
    
    for asset in assets:
        current_price = float(asset.valuation)
        
        for day_offset in range(days, 0, -1):
            # Add random time within the day (market hours simulation)
            random_hour = random.randint(8, 17)  # 8 AM to 5 PM
            random_minute = random.randint(0, 59)
            random_second = random.randint(0, 59)
            
            date = now - timedelta(days=day_offset)
            date = date.replace(hour=random_hour, minute=random_minute, second=random_second)
            
            # Random daily price movement (-3% to +3%)
            change = random.uniform(-0.03, 0.03)
            current_price = current_price * (1 + change)
            
            # Random volume
            volume = random.uniform(1000, 50000)
            
            history_entries.append(AssetPriceHistory(
                asset=asset,
                price=Decimal(str(round(current_price, 8))),
                volume=Decimal(str(round(volume, 2))),
                recorded_at=date
            ))
    
    # Bulk create for performance
    AssetPriceHistory.objects.bulk_create(history_entries, batch_size=1000)
    print(f"  ✓ Created {len(history_entries)} price history records")


def simulate_trades(users: list[User], assets: list[Asset], trade_count: int = 50):
    """Simulate some trading activity to populate portfolios."""
    print(f"\nSimulating {trade_count} trades...")
    
    from apps.catalog.services import InvestService
    
    invest_service = InvestService()
    successful_trades = 0
    
    for _ in range(trade_count):
        user = random.choice(users)
        
        # Get assets from user's tenant only
        tenant_assets = [a for a in assets if a.tenant_id == user.tenant_id]
        if not tenant_assets:
            continue
            
        asset = random.choice(tenant_assets)
        
        # Random share amount (0.1 to 10 shares)
        shares = Decimal(str(round(random.uniform(0.1, 10), 8)))
        
        try:
            invest_service.invest(
                user=user,
                asset=asset,
                shares=shares
            )
            successful_trades += 1
        except Exception as e:
            # Skip failed trades (insufficient funds, policy violations, etc.)
            pass
    
    print(f"  ✓ Completed {successful_trades} successful trades")


# ============================================================================
# Main
# ============================================================================

@transaction.atomic
def seed():
    """Run the full seeding process."""
    print("=" * 60)
    print("EquiShard Database Seeding")
    print("=" * 60)
    
    # Always check/ensure admin exists first (Idempotent)
    create_admin()

    # Check if data already exists
    if Tenant.objects.exists():
        print("\n⚠️  Tenants already exist. Skipping asset/user generation.")
        print("   To re-seed fully, run: python manage.py flush")
        return
    
    tenants = create_tenants()
    users = create_users(tenants)
    # Admin created above
    assets = create_assets(tenants)
    create_price_history(assets)
    simulate_trades(users, assets)
    
    print("\n" + "=" * 60)
    print("✅ Seeding complete!")
    print("=" * 60)
    print(f"\nCreated:")
    print(f"  - {len(tenants)} tenants")
    print(f"  - {len(users)} users")
    print(f"  - {len(assets)} assets")
    print(f"  - 30 days of price history")
    print(f"\nTest credentials:")
    for tenant in TENANTS:
        print(f"  - investor1_{tenant['slug']} / password123")


if __name__ == "__main__":
    seed()
