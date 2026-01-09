"""
Store API Endpoints

Public browsing endpoints for assets and marketplace.
"""

from typing import List, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from api.dependencies import CurrentUser, get_optional_user


router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class AssetListItem(BaseModel):
    """Asset for listing view."""
    id: int
    symbol: str
    name: str
    asset_type: str
    valuation: float
    risk_level: int
    accreditation_required: bool
    available_shares: float
    minimum_investment: float
    image_url: Optional[str] = None
    price_history: List[float] = []


class AssetDetail(BaseModel):
    """Detailed asset information."""
    id: int
    symbol: str
    name: str
    description: str
    asset_type: str
    valuation: float
    total_shares: float
    available_shares: float
    sold_shares: float
    risk_level: int
    accreditation_required: bool
    minimum_investment: float
    market_cap: float
    market_cap: float
    image_url: Optional[str] = None
    user_shares: Optional[float] = 0.0


class PriceHistoryPoint(BaseModel):
    """Price history data point."""
    date: str
    price: float
    volume: float


class MarketStats(BaseModel):
    """Marketplace statistics."""
    total_assets: int
    total_market_cap: float
    total_investors: int
    total_volume_24h: float


# ============================================================================
# Database helper functions (sync)
# ============================================================================

def _list_assets_sync(
    tenant_id: Optional[int],
    asset_type: Optional[str],
    risk_level: Optional[int],
    min_price: Optional[float],
    max_price: Optional[float],
    sort_by: str,
    order: str,
    limit: int,
    offset: int,
) -> List[tuple]:
    from django.db import connection
    
    conditions = ["a.is_active = true"]
    params = []
    
    if tenant_id:
        conditions.append("a.tenant_id = %s")
        params.append(tenant_id)
    
    if asset_type:
        conditions.append("a.asset_type = %s")
        params.append(asset_type.upper())
    
    if risk_level:
        conditions.append("a.risk_level = %s")
        params.append(risk_level)
    
    if min_price is not None:
        conditions.append("a.valuation >= %s")
        params.append(min_price)
    
    if max_price is not None:
        conditions.append("a.valuation <= %s")
        params.append(max_price)
    
    where_clause = " AND ".join(conditions)
    order_direction = "ASC" if order == "asc" else "DESC"
    
    
    # Check if we are running in simple mode (no complex aggregation)
    # Using a subquery for array aggregation of recent prices
    query = f"""
        SELECT 
            a.id,
            a.symbol,
            a.name,
            a.asset_type,
            a.valuation,
            a.risk_level,
            a.accreditation_required,
            ai.available_shares,
            a.minimum_investment,
            a.image_url,
            (
                SELECT ARRAY_AGG(ph.price)
                FROM (
                    SELECT price
                    FROM asset_price_history ph
                    WHERE ph.asset_id = a.id
                    ORDER BY ph.recorded_at DESC
                    LIMIT 6
                ) ph
            ) as recent_prices
        FROM assets a
        LEFT JOIN asset_inventory ai ON a.id = ai.asset_id
        WHERE {where_clause}
        ORDER BY a.{sort_by} {order_direction}
        LIMIT %s OFFSET %s
    """
    
    params.extend([limit, offset])
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def _get_asset_sync(asset_id: int) -> Optional[tuple]:
    from django.db import connection
    
    query = """
        SELECT 
            a.id,
            a.symbol,
            a.name,
            a.description,
            a.asset_type,
            a.valuation,
            a.total_shares,
            ai.available_shares,
            ai.sold_shares,
            a.risk_level,
            a.accreditation_required,
            a.minimum_investment,
            a.image_url
        FROM assets a
        LEFT JOIN asset_inventory ai ON a.id = ai.asset_id
        WHERE a.id = %s AND a.is_active = true
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [asset_id])
        return cursor.fetchone()


def _get_asset_position_sync(asset_id: int, user_id: int) -> float:
    from django.db import connection
    
    query = """
        SELECT shares
        FROM user_positions
        WHERE asset_id = %s AND user_id = %s
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [asset_id, user_id])
        row = cursor.fetchone()
        return float(row[0]) if row else 0.0


def _get_price_history_sync(asset_id: int, days: int) -> List[tuple]:
    from django.db import connection
    from datetime import datetime, timedelta
    
    start_date = datetime.now() - timedelta(days=days)
    
    query = """
        SELECT 
            recorded_at,
            price,
            volume
        FROM asset_price_history
        WHERE asset_id = %s
          AND recorded_at >= %s
        ORDER BY recorded_at
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [asset_id, start_date])
        return cursor.fetchall()


def _get_market_stats_sync() -> tuple:
    from django.db import connection
    from datetime import datetime, timedelta
    
    query1 = """
        SELECT 
            COUNT(*) as total_assets,
            COALESCE(SUM(a.valuation * a.total_shares), 0) as total_market_cap
        FROM assets a
        WHERE a.is_active = true
    """
    
    query2 = """
        SELECT COUNT(DISTINCT user_id) as total_investors
        FROM user_positions
        WHERE shares > 0
    """
    
    query3 = """
        SELECT COALESCE(SUM(ABS(tl.amount)), 0) as volume
        FROM transaction_lines tl
        JOIN journal_entries je ON tl.journal_entry_id = je.id
        WHERE je.entry_type = 'INVESTMENT'
          AND je.posted = true
          AND je.timestamp >= %s
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query1)
        row1 = cursor.fetchone()
        
        cursor.execute(query2)
        row2 = cursor.fetchone()
        
        cursor.execute(query3, [datetime.now() - timedelta(hours=24)])
        row3 = cursor.fetchone()
    
    return (row1, row2, row3)


def _list_asset_types_sync() -> List[tuple]:
    from django.db import connection
    
    query = """
        SELECT DISTINCT asset_type, COUNT(*) as count
        FROM assets
        WHERE is_active = true
        GROUP BY asset_type
        ORDER BY count DESC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/assets", response_model=List[AssetListItem])
async def list_assets(
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
    asset_type: Optional[str] = Query(default=None),
    risk_level: Optional[int] = Query(default=None, ge=1, le=5),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    sort_by: str = Query(default="name", pattern="^(name|valuation|risk_level)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    List available assets with filtering and pagination.
    
    Public endpoint - no authentication required.
    """
    tenant_id = current_user.tenant_id if current_user else None
    
    rows = await sync_to_async(_list_assets_sync)(
        tenant_id, asset_type, risk_level, min_price, max_price,
        sort_by, order, limit, offset
    )
    
    return [
        AssetListItem(
            id=row[0],
            symbol=row[1],
            name=row[2],
            asset_type=row[3].replace('_', ' ').title(),
            valuation=float(row[4]),
            risk_level=row[5],
            accreditation_required=row[6],
            available_shares=float(row[7] or 0),
            minimum_investment=float(row[8]),
            image_url=row[9] or None,
            price_history=[float(p) for p in (row[10] or [])][::-1]  # Reverse to get chronological order
        )
        for row in rows
    ]


class AssetDetail(BaseModel):
    """Detailed asset information."""
    id: int
    symbol: str
    name: str
    description: str
    asset_type: str
    valuation: float
    total_shares: float
    available_shares: float
    sold_shares: float
    risk_level: int
    accreditation_required: bool
    minimum_investment: float
    market_cap: float
    image_url: Optional[str] = None
    user_shares: Optional[float] = 0.0


class PriceHistoryPoint(BaseModel):
    """Price history data point."""
    date: str
    price: float
    volume: float


@router.get("/assets/{asset_id}", response_model=AssetDetail)
async def get_asset(
    asset_id: int,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """Get detailed asset information."""
    row = await sync_to_async(_get_asset_sync)(asset_id)
    
    if not row:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    user_shares = 0.0
    if current_user:
        user_shares = await sync_to_async(_get_asset_position_sync)(asset_id, current_user.id)
    
    valuation = float(row[5])
    total_shares = float(row[6])
    
    return AssetDetail(
        id=row[0],
        symbol=row[1],
        name=row[2],
        description=row[3] or "",
        asset_type=row[4].replace('_', ' ').title(),
        valuation=valuation,
        total_shares=total_shares,
        available_shares=float(row[7] or 0),
        sold_shares=float(row[8] or 0),
        risk_level=row[9],
        accreditation_required=row[10],
        minimum_investment=float(row[11]),
        market_cap=valuation * total_shares,
        image_url=row[12] or None,
        user_shares=user_shares
    )


@router.get("/assets/{asset_id}/price-history", response_model=List[PriceHistoryPoint])
async def get_price_history(
    asset_id: int,
    days: int = Query(default=30, ge=1, le=365),
):
    """Get historical price data for an asset."""
    rows = await sync_to_async(_get_price_history_sync)(asset_id, days)
    
    return [
        PriceHistoryPoint(
            date=row[0].strftime("%Y-%m-%d %H:%M:%S") if hasattr(row[0], 'strftime') else str(row[0]),
            price=float(row[1]),
            volume=float(row[2])
        )
        for row in rows
    ]


@router.get("/stats", response_model=MarketStats)
async def get_market_stats():
    """Get marketplace statistics."""
    row1, row2, row3 = await sync_to_async(_get_market_stats_sync)()
    
    return MarketStats(
        total_assets=row1[0] or 0,
        total_market_cap=float(row1[1] or 0),
        total_investors=row2[0] or 0,
        total_volume_24h=float(row3[0] or 0)
    )


@router.get("/asset-types")
async def list_asset_types():
    """Get list of available asset types."""
    rows = await sync_to_async(_list_asset_types_sync)()
    
    return [
        {
            "value": row[0],
            "label": row[0].replace('_', ' ').title(),
            "count": row[1]
        }
        for row in rows
    ]
