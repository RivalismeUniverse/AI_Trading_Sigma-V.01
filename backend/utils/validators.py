"""
Input Validators
Validation functions for API inputs and trading parameters
"""

from typing import Tuple, Optional
import re

from utils.constants import ALLOWED_SYMBOLS, MAX_ALLOWED_LEVERAGE


def validate_symbol(symbol: str) -> Tuple[bool, Optional[str]]:
    """Validate trading symbol"""
    if not symbol:
        return False, "Symbol is required"
    
    if symbol not in ALLOWED_SYMBOLS:
        return False, f"Symbol must be one of: {ALLOWED_SYMBOLS}"
    
    return True, None


def validate_leverage(leverage: int) -> Tuple[bool, Optional[str]]:
    """Validate leverage value"""
    if not isinstance(leverage, int):
        return False, "Leverage must be an integer"
    
    if leverage < 1:
        return False, "Leverage must be at least 1"
    
    if leverage > MAX_ALLOWED_LEVERAGE:
        return False, f"Leverage cannot exceed {MAX_ALLOWED_LEVERAGE}x"
    
    return True, None


def validate_amount(amount: float) -> Tuple[bool, Optional[str]]:
    """Validate trade amount"""
    if not isinstance(amount, (int, float)):
        return False, "Amount must be a number"
    
    if amount <= 0:
        return False, "Amount must be greater than 0"
    
    return True, None


def validate_price(price: float) -> Tuple[bool, Optional[str]]:
    """Validate price value"""
    if not isinstance(price, (int, float)):
        return False, "Price must be a number"
    
    if price <= 0:
        return False, "Price must be greater than 0"
    
    return True, None


def validate_timeframe(timeframe: str) -> Tuple[bool, Optional[str]]:
    """Validate timeframe"""
    valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
    
    if timeframe not in valid_timeframes:
        return False, f"Timeframe must be one of: {valid_timeframes}"
    
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, None


def validate_strategy_parameters(params: dict) -> Tuple[bool, Optional[str]]:
    """Validate strategy parameters"""
    required_fields = ['symbols', 'timeframe', 'leverage']
    
    for field in required_fields:
        if field not in params:
            return False, f"Missing required field: {field}"
    
    # Validate symbols
    for symbol in params.get('symbols', []):
        valid, error = validate_symbol(symbol)
        if not valid:
            return False, error
    
    # Validate timeframe
    valid, error = validate_timeframe(params.get('timeframe'))
    if not valid:
        return False, error
    
    # Validate leverage
    valid, error = validate_leverage(params.get('leverage'))
    if not valid:
        return False, error
    
    return True, None


# Export
__all__ = [
    'validate_symbol',
    'validate_leverage',
    'validate_amount',
    'validate_price',
    'validate_timeframe',
    'validate_email',
    'validate_strategy_parameters'
    ]
