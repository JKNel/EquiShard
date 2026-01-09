"""
Decimal utilities for financial calculations.

All money and share math should use these helpers to ensure precision.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union


# Standard precision for money (2 decimal places)
MONEY_PRECISION = Decimal('0.01')

# Standard precision for shares (8 decimal places for fractional)
SHARE_PRECISION = Decimal('0.00000001')


def to_decimal(value: Union[str, int, float, Decimal]) -> Decimal:
    """
    Convert any numeric value to Decimal safely.
    
    Args:
        value: The value to convert
        
    Returns:
        Decimal representation
        
    Raises:
        ValueError: If the value cannot be converted
    """
    if isinstance(value, Decimal):
        return value
    
    try:
        if isinstance(value, float):
            # Convert float via string to avoid precision issues
            return Decimal(str(value))
        return Decimal(value)
    except (InvalidOperation, TypeError) as e:
        raise ValueError(f"Cannot convert {value!r} to Decimal: {e}")


def round_money(amount: Decimal) -> Decimal:
    """
    Round a monetary amount to 2 decimal places.
    
    Uses banker's rounding (ROUND_HALF_UP).
    """
    return amount.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def round_shares(shares: Decimal) -> Decimal:
    """
    Round share quantity to 8 decimal places.
    """
    return shares.quantize(SHARE_PRECISION, rounding=ROUND_HALF_UP)


def is_positive(value: Decimal) -> bool:
    """Check if a Decimal value is positive."""
    return value > Decimal('0')


def is_zero(value: Decimal) -> bool:
    """Check if a Decimal value is zero."""
    return value == Decimal('0')


def format_currency(amount: Decimal, symbol: str = '$') -> str:
    """
    Format a Decimal as a currency string.
    
    Example: format_currency(Decimal('1234.56')) -> '$1,234.56'
    """
    rounded = round_money(amount)
    return f"{symbol}{rounded:,.2f}"


def format_shares(shares: Decimal) -> str:
    """
    Format a share quantity, removing unnecessary trailing zeros.
    
    Example: format_shares(Decimal('1.50000000')) -> '1.5'
    """
    normalized = shares.normalize()
    return str(normalized)


def calculate_percentage(part: Decimal, whole: Decimal) -> Decimal:
    """
    Calculate percentage of a part relative to whole.
    
    Returns percentage as a Decimal (e.g., 25.5 for 25.5%).
    """
    if is_zero(whole):
        return Decimal('0')
    return round_money((part / whole) * Decimal('100'))
