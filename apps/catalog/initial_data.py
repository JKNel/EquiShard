from apps.catalog.models import AssetType

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
