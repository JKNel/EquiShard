"""
Analytics API Endpoints

Chart-optimized endpoints for frontend visualization.
Returns data formatted for Recharts/Chart.js.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.dependencies import CurrentUser, get_current_user


router = APIRouter()


# ============================================================================
# Response Models (Pydantic)
# ============================================================================

class PortfolioGrowthPoint(BaseModel):
    """Data point for portfolio growth chart."""
    date: str
    value: float


class AllocationItem(BaseModel):
    """Data point for allocation pie chart."""
    name: str
    value: float
    percentage: float


class PositionItem(BaseModel):
    """User position in an asset."""
    asset_id: int
    symbol: str
    name: str
    asset_type: str
    shares: float
    average_cost: float
    current_price: float
    current_value: float
    profit_loss: float
    profit_loss_percent: float


class PortfolioSummary(BaseModel):
    """Summary of user's portfolio."""
    total_value: float
    total_invested: float
    total_profit_loss: float
    profit_loss_percent: float
    positions_count: int


# ============================================================================
# Database helper functions (sync)
# ============================================================================

def _get_portfolio_growth_sync(user_id: int, days: int) -> List[tuple]:
    from django.db import connection
    
    start_date = datetime.now() - timedelta(days=days)
    
    query = """
        SELECT 
            DATE(tl.created_at) as date,
            tl.balance_snapshot as value
        FROM transaction_lines tl
        JOIN ledger_accounts la ON tl.account_id = la.id
        JOIN journal_entries je ON tl.journal_entry_id = je.id
        WHERE la.owner_id = %s
          AND la.category = 'USER_WALLET'
          AND je.posted = true
          AND tl.created_at >= %s
        ORDER BY tl.created_at
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [user_id, start_date])
        return cursor.fetchall()


def _get_allocation_sync(user_id: int) -> List[tuple]:
    from django.db import connection
    
    query = """
        SELECT 
            a.asset_type,
            SUM(up.shares * a.valuation) as total_value
        FROM user_positions up
        JOIN assets a ON up.asset_id = a.id
        WHERE up.user_id = %s
          AND up.shares > 0
        GROUP BY a.asset_type
        ORDER BY total_value DESC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [user_id])
        return cursor.fetchall()


def _get_positions_sync(user_id: int) -> List[tuple]:
    from django.db import connection
    
    query = """
        SELECT 
            a.id,
            a.symbol,
            a.name,
            a.asset_type,
            up.shares,
            up.average_cost,
            a.valuation as current_price
        FROM user_positions up
        JOIN assets a ON up.asset_id = a.id
        WHERE up.user_id = %s
          AND up.shares > 0
        ORDER BY (up.shares * a.valuation) DESC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [user_id])
        return cursor.fetchall()


def _get_portfolio_summary_sync(user_id: int) -> tuple:
    from django.db import connection
    
    query = """
        SELECT 
            COUNT(*) as positions_count,
            COALESCE(SUM(up.shares * a.valuation), 0) as total_value,
            COALESCE(SUM(up.shares * up.average_cost), 0) as total_invested
        FROM user_positions up
        JOIN assets a ON up.asset_id = a.id
        WHERE up.user_id = %s
          AND up.shares > 0
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [user_id])
        return cursor.fetchone()


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/portfolio-growth", response_model=List[PortfolioGrowthPoint])
async def get_portfolio_growth(
    current_user: CurrentUser = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=365),
):
    """
    Get portfolio value over time for growth chart.
    
    Returns array of date/value pairs for line chart visualization.
    """
    rows = await sync_to_async(_get_portfolio_growth_sync)(current_user.id, days)
    
    # Aggregate by date (take last value of each day)
    daily_values: Dict[str, float] = {}
    for row in rows:
        date_str = row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0])
        daily_values[date_str] = float(row[1])
    
    return [
        PortfolioGrowthPoint(date=date, value=value)
        for date, value in sorted(daily_values.items())
    ]


@router.get("/allocation", response_model=List[AllocationItem])
async def get_allocation(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get portfolio allocation by asset type for pie chart.
    
    Returns breakdown of investments by category.
    """
    rows = await sync_to_async(_get_allocation_sync)(current_user.id)
    
    if not rows:
        return []
    
    total = sum(float(row[1]) for row in rows)
    
    return [
        AllocationItem(
            name=row[0].replace('_', ' ').title(),
            value=float(row[1]),
            percentage=round(float(row[1]) / total * 100, 2) if total > 0 else 0
        )
        for row in rows
    ]


@router.get("/positions", response_model=List[PositionItem])
async def get_positions(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get all user positions with profit/loss calculations."""
    rows = await sync_to_async(_get_positions_sync)(current_user.id)
    
    positions = []
    for row in rows:
        shares = float(row[4])
        avg_cost = float(row[5])
        current_price = float(row[6])
        
        total_invested = shares * avg_cost
        current_value = shares * current_price
        profit_loss = current_value - total_invested
        profit_loss_percent = (profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        positions.append(PositionItem(
            asset_id=row[0],
            symbol=row[1],
            name=row[2],
            asset_type=row[3].replace('_', ' ').title(),
            shares=shares,
            average_cost=avg_cost,
            current_price=current_price,
            current_value=round(current_value, 2),
            profit_loss=round(profit_loss, 2),
            profit_loss_percent=round(profit_loss_percent, 2)
        ))
    
    return positions


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get portfolio summary with totals."""
    row = await sync_to_async(_get_portfolio_summary_sync)(current_user.id)
    
    positions_count = row[0] or 0
    total_value = float(row[1] or 0)
    total_invested = float(row[2] or 0)
    
    profit_loss = total_value - total_invested
    profit_loss_percent = (profit_loss / total_invested * 100) if total_invested > 0 else 0
    
    return PortfolioSummary(
        total_value=round(total_value, 2),
        total_invested=round(total_invested, 2),
        total_profit_loss=round(profit_loss, 2),
        profit_loss_percent=round(profit_loss_percent, 2),
        positions_count=positions_count
    )
