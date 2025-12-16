"""
Helper Functions
Utility functions used across the application
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import hashlib
import uuid


def generate_order_id() -> str:
    """Generate unique order ID"""
    return f"ORD-{uuid.uuid4().hex[:12].upper()}"


def generate_trade_id() -> str:
    """Generate unique trade ID"""
    return f"TRD-{uuid.uuid4().hex[:12].upper()}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    return f"${amount:,.2f}" if currency == "USD" else f"{amount:,.2f} {currency}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage"""
    return f"{value:.{decimals}f}%"


def timestamp_to_datetime(timestamp: int) -> datetime:
    """Convert Unix timestamp to datetime"""
    return datetime.fromtimestamp(timestamp / 1000)


def datetime_to_timestamp(dt: datetime) -> int:
    """Convert datetime to Unix timestamp"""
    return int(dt.timestamp() * 1000)


def calculate_pnl(
    entry_price: float,
    exit_price: float,
    position_size: float,
    side: str
) -> float:
    """
    Calculate P&L for a trade
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        position_size: Position size
        side: 'long' or 'short'
        
    Returns:
        P&L amount
    """
    if side.lower() == 'long':
        return (exit_price - entry_price) * position_size
    else:  # short
        return (entry_price - exit_price) * position_size


def calculate_roe(
    pnl: float,
    margin: float
) -> float:
    """
    Calculate Return on Equity (ROE)
    
    Args:
        pnl: Profit/Loss
        margin: Initial margin
        
    Returns:
        ROE as percentage
    """
    if margin == 0:
        return 0.0
    return (pnl / margin) * 100


def hash_string(text: str) -> str:
    """Generate SHA256 hash of string"""
    return hashlib.sha256(text.encode()).hexdigest()


def truncate_string(text: str, length: int = 100) -> str:
    """Truncate string to specified length"""
    if len(text) <= length:
        return text
    return text[:length - 3] + "..."


def parse_timeframe_to_seconds(timeframe: str) -> int:
    """
    Parse timeframe string to seconds
    
    Args:
        timeframe: e.g., '5m', '1h', '1d'
        
    Returns:
        Seconds
    """
    units = {
        'm': 60,
        'h': 3600,
        'd': 86400
    }
    
    if not timeframe:
        return 300  # Default 5 minutes
    
    unit = timeframe[-1]
    value = int(timeframe[:-1])
    
    return value * units.get(unit, 60)


def get_date_range(days: int = 7) -> tuple:
    """Get date range (start, end)"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def batch_list(items: List, batch_size: int) -> List[List]:
    """Split list into batches"""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default value"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp value between min and max"""
    return max(min_value, min(value, max_value))


def moving_average(values: List[float], window: int) -> List[float]:
    """Calculate simple moving average"""
    if len(values) < window:
        return values
    
    result = []
    for i in range(len(values)):
        if i < window - 1:
            result.append(values[i])
        else:
            avg = sum(values[i - window + 1:i + 1]) / window
            result.append(avg)
    
    return result


def calculate_drawdown(equity_curve: List[float]) -> float:
    """Calculate maximum drawdown from equity curve"""
    if not equity_curve:
        return 0.0
    
    peak = equity_curve[0]
    max_dd = 0.0
    
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)
    
    return max_dd * 100


# Export
__all__ = [
    'generate_order_id',
    'generate_trade_id',
    'calculate_percentage_change',
    'format_currency',
    'format_percentage',
    'timestamp_to_datetime',
    'datetime_to_timestamp',
    'calculate_pnl',
    'calculate_roe',
    'hash_string',
    'truncate_string',
    'parse_timeframe_to_seconds',
    'get_date_range',
    'batch_list',
    'flatten_dict',
    'safe_divide',
    'clamp',
    'moving_average',
    'calculate_drawdown'
]
