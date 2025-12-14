"""
Helper utilities for trading system.
Common functions used across the application.
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
import json
import hashlib
import time

def round_to_precision(value: float, precision: int = 8) -> float:
    """
    Round value to specified decimal precision
    
    Args:
        value: Value to round
        precision: Number of decimal places
        
    Returns:
        Rounded value
    """
    decimal_value = Decimal(str(value))
    precision_str = f"0.{'0' * precision}"
    return float(decimal_value.quantize(Decimal(precision_str), rounding=ROUND_DOWN))

def calculate_position_size(
    balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss: float,
    leverage: float = 1.0
) -> float:
    """
    Calculate position size based on risk management
    
    Args:
        balance: Account balance
        risk_percent: Risk per trade (0.01 = 1%)
        entry_price: Entry price
        stop_loss: Stop loss price
        leverage: Leverage multiplier
        
    Returns:
        Position size in base currency
    """
    risk_amount = balance * risk_percent
    price_risk = abs(entry_price - stop_loss)
    risk_per_unit = price_risk / entry_price
    
    position_size = (risk_amount / risk_per_unit) * leverage / entry_price
    
    return round_to_precision(position_size, 6)

def calculate_pnl(
    side: str,
    entry_price: float,
    exit_price: float,
    quantity: float,
    leverage: float = 1.0
) -> Dict[str, float]:
    """
    Calculate P&L for a trade
    
    Args:
        side: 'long' or 'short'
        entry_price: Entry price
        exit_price: Exit price
        quantity: Position size
        leverage: Leverage used
        
    Returns:
        Dictionary with pnl, pnl_percent, roi
    """
    if side.lower() in ['buy', 'long']:
        pnl = (exit_price - entry_price) * quantity
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
    else:  # short
        pnl = (entry_price - exit_price) * quantity
        pnl_percent = ((entry_price - exit_price) / entry_price) * 100
    
    # Apply leverage
    roi = pnl_percent * leverage
    
    return {
        'pnl': round_to_precision(pnl, 2),
        'pnl_percent': round_to_precision(pnl_percent, 2),
        'roi': round_to_precision(roi, 2)
    }

def calculate_fees(
    quantity: float,
    price: float,
    fee_rate: float = 0.0005  # 0.05% typical
) -> float:
    """Calculate trading fees"""
    trade_value = quantity * price
    return round_to_precision(trade_value * fee_rate, 2)

def format_currency(value: float, currency: str = 'USDT') -> str:
    """Format value as currency string"""
    if abs(value) >= 1000:
        return f"${value:,.2f} {currency}"
    else:
        return f"${value:.2f} {currency}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format value as percentage string"""
    sign = '+' if value > 0 else ''
    return f"{sign}{value:.{decimals}f}%"

def parse_timeframe_to_seconds(timeframe: str) -> int:
    """
    Convert timeframe string to seconds
    
    Args:
        timeframe: e.g., '1m', '5m', '1h', '1d'
        
    Returns:
        Seconds
    """
    units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    if len(timeframe) < 2:
        raise ValueError(f"Invalid timeframe: {timeframe}")
    
    number = int(timeframe[:-1])
    unit = timeframe[-1].lower()
    
    if unit not in units:
        raise ValueError(f"Invalid timeframe unit: {unit}")
    
    return number * units[unit]

def get_timeframe_interval(timeframe: str) -> timedelta:
    """Get timedelta for a timeframe string"""
    seconds = parse_timeframe_to_seconds(timeframe)
    return timedelta(seconds=seconds)

def generate_trade_id(symbol: str, timestamp: Optional[int] = None) -> str:
    """
    Generate unique trade ID
    
    Args:
        symbol: Trading symbol
        timestamp: Unix timestamp (optional)
        
    Returns:
        Unique trade ID
    """
    if timestamp is None:
        timestamp = int(time.time() * 1000)
    
    data = f"{symbol}_{timestamp}_{time.time()}"
    hash_obj = hashlib.md5(data.encode())
    return f"TRADE_{hash_obj.hexdigest()[:12].upper()}"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that returns default on zero denominator"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default

def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def moving_average(values: List[float], period: int) -> List[float]:
    """Calculate simple moving average"""
    if len(values) < period:
        return []
    
    result = []
    for i in range(len(values) - period + 1):
        avg = sum(values[i:i + period]) / period
        result.append(avg)
    
    return result

def exponential_moving_average(values: List[float], period: int) -> List[float]:
    """Calculate exponential moving average"""
    if len(values) < period:
        return []
    
    multiplier = 2 / (period + 1)
    ema = [sum(values[:period]) / period]  # Start with SMA
    
    for i in range(period, len(values)):
        ema_value = (values[i] * multiplier) + (ema[-1] * (1 - multiplier))
        ema.append(ema_value)
    
    return ema

def calculate_volatility(prices: List[float], period: int = 20) -> float:
    """Calculate price volatility (standard deviation)"""
    if len(prices) < period:
        return 0.0
    
    recent_prices = prices[-period:]
    mean = sum(recent_prices) / len(recent_prices)
    variance = sum((p - mean) ** 2 for p in recent_prices) / len(recent_prices)
    
    return variance ** 0.5

def is_market_hours(timezone: str = 'UTC') -> bool:
    """
    Check if within trading hours (crypto trades 24/7)
    Always returns True for crypto
    """
    return True  # Crypto markets are always open

def time_until_next_candle(timeframe: str, current_time: Optional[datetime] = None) -> int:
    """
    Calculate seconds until next candle closes
    
    Args:
        timeframe: e.g., '5m', '1h'
        current_time: Current datetime (optional)
        
    Returns:
        Seconds until next candle
    """
    if current_time is None:
        current_time = datetime.utcnow()
    
    interval_seconds = parse_timeframe_to_seconds(timeframe)
    current_timestamp = int(current_time.timestamp())
    
    next_candle = ((current_timestamp // interval_seconds) + 1) * interval_seconds
    
    return next_candle - current_timestamp

def format_timestamp(timestamp: Union[int, float, datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp to string"""
    if isinstance(timestamp, (int, float)):
        # Assume milliseconds if > 10 digits
        if timestamp > 10000000000:
            timestamp = timestamp / 1000
        dt = datetime.fromtimestamp(timestamp)
    else:
        dt = timestamp
    
    return dt.strftime(format_str)

def parse_json_safe(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def truncate_string(s: str, max_length: int = 50, suffix: str = '...') -> str:
    """Truncate string to max length"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix

def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe ratio
    
    Args:
        returns: List of returns (decimal, e.g., 0.02 for 2%)
        risk_free_rate: Risk-free rate (annualized)
        
    Returns:
        Sharpe ratio
    """
    if not returns:
        return 0.0
    
    mean_return = sum(returns) / len(returns)
    
    if len(returns) < 2:
        return 0.0
    
    std_dev = (sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)) ** 0.5
    
    if std_dev == 0:
        return 0.0
    
    # Annualize assuming daily returns
    sharpe = ((mean_return - risk_free_rate) * (252 ** 0.5)) / std_dev
    
    return round_to_precision(sharpe, 2)

def calculate_max_drawdown(equity_curve: List[float]) -> Dict[str, float]:
    """
    Calculate maximum drawdown from equity curve
    
    Args:
        equity_curve: List of equity values
        
    Returns:
        Dictionary with max_drawdown, max_drawdown_percent, peak, trough
    """
    if not equity_curve:
        return {'max_drawdown': 0.0, 'max_drawdown_percent': 0.0, 'peak': 0.0, 'trough': 0.0}
    
    peak = equity_curve[0]
    max_drawdown = 0.0
    max_drawdown_percent = 0.0
    peak_value = peak
    trough_value = peak
    
    for value in equity_curve:
        if value > peak:
            peak = value
        
        drawdown = peak - value
        drawdown_percent = (drawdown / peak) * 100 if peak > 0 else 0
        
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_drawdown_percent = drawdown_percent
            peak_value = peak
            trough_value = value
    
    return {
        'max_drawdown': round_to_precision(max_drawdown, 2),
        'max_drawdown_percent': round_to_precision(max_drawdown_percent, 2),
        'peak': round_to_precision(peak_value, 2),
        'trough': round_to_precision(trough_value, 2)
    }

def calculate_win_rate(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate win rate from trades
    
    Args:
        trades: List of trade dictionaries with 'pnl' field
        
    Returns:
        Dictionary with win_rate, total_trades, winning_trades, losing_trades
    """
    if not trades:
        return {
            'win_rate': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0
        }
    
    winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
    total_trades = len(trades)
    
    return {
        'win_rate': round_to_precision((winning_trades / total_trades) * 100, 2),
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': total_trades - winning_trades
    }

# Example usage
if __name__ == "__main__":
    # Test helpers
    print("Position size:", calculate_position_size(
        balance=1000,
        risk_percent=0.02,
        entry_price=50000,
        stop_loss=49000,
        leverage=10
    ))
    
    print("P&L:", calculate_pnl(
        side='long',
        entry_price=50000,
        exit_price=51000,
        quantity=0.1,
        leverage=10
    ))
    
    print("Trade ID:", generate_trade_id('BTC/USDT:USDT'))
    print("Timeframe seconds:", parse_timeframe_to_seconds('5m'))
    print("Time until next 5m candle:", time_until_next_candle('5m'), "seconds")
