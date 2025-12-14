"""
Input validation utilities for trading system.
Validates user inputs, trading parameters, and API responses.
"""
from typing import Dict, Any, Optional, List
from decimal import Decimal
import re
from datetime import datetime

class ValidationError(Exception):
    """Custom validation error"""
    pass

class TradingValidator:
    """Validates trading-related inputs"""
    
    # WEEX Hackathon allowed pairs
    ALLOWED_PAIRS = [
        'ADA/USDT:USDT',
        'SOL/USDT:USDT', 
        'LTC/USDT:USDT',
        'DOGE/USDT:USDT',
        'BTC/USDT:USDT',
        'ETH/USDT:USDT',
        'XRP/USDT:USDT',
        'BNB/USDT:USDT'
    ]
    
    VALID_TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d']
    VALID_ORDER_TYPES = ['market', 'limit']
    VALID_SIDES = ['buy', 'sell', 'long', 'short']
    
    MIN_LEVERAGE = 1
    MAX_LEVERAGE = 20  # WEEX hackathon limit
    
    MIN_POSITION_SIZE = 0.001  # Minimum position size in base currency
    MAX_RISK_PERCENT = 0.1  # 10% max per trade
    
    @classmethod
    def validate_symbol(cls, symbol: str) -> str:
        """Validate trading symbol"""
        if not symbol:
            raise ValidationError("Symbol cannot be empty")
        
        # Normalize symbol format
        symbol = symbol.upper().strip()
        
        # Check if in allowed list
        if symbol not in cls.ALLOWED_PAIRS:
            raise ValidationError(
                f"Symbol {symbol} not allowed. Must be one of: {', '.join(cls.ALLOWED_PAIRS)}"
            )
        
        return symbol
    
    @classmethod
    def validate_timeframe(cls, timeframe: str) -> str:
        """Validate timeframe"""
        if timeframe not in cls.VALID_TIMEFRAMES:
            raise ValidationError(
                f"Invalid timeframe {timeframe}. Must be one of: {', '.join(cls.VALID_TIMEFRAMES)}"
            )
        return timeframe
    
    @classmethod
    def validate_leverage(cls, leverage: float) -> float:
        """Validate leverage amount"""
        if not isinstance(leverage, (int, float)):
            raise ValidationError("Leverage must be a number")
        
        if leverage < cls.MIN_LEVERAGE or leverage > cls.MAX_LEVERAGE:
            raise ValidationError(
                f"Leverage must be between {cls.MIN_LEVERAGE}x and {cls.MAX_LEVERAGE}x"
            )
        
        return float(leverage)
    
    @classmethod
    def validate_order_side(cls, side: str) -> str:
        """Validate order side"""
        side = side.lower().strip()
        if side not in cls.VALID_SIDES:
            raise ValidationError(
                f"Invalid side {side}. Must be one of: {', '.join(cls.VALID_SIDES)}"
            )
        return side
    
    @classmethod
    def validate_order_type(cls, order_type: str) -> str:
        """Validate order type"""
        order_type = order_type.lower().strip()
        if order_type not in cls.VALID_ORDER_TYPES:
            raise ValidationError(
                f"Invalid order type {order_type}. Must be one of: {', '.join(cls.VALID_ORDER_TYPES)}"
            )
        return order_type
    
    @classmethod
    def validate_quantity(cls, quantity: float, symbol: str) -> float:
        """Validate order quantity"""
        if not isinstance(quantity, (int, float, Decimal)):
            raise ValidationError("Quantity must be a number")
        
        quantity = float(quantity)
        
        if quantity <= 0:
            raise ValidationError("Quantity must be positive")
        
        if quantity < cls.MIN_POSITION_SIZE:
            raise ValidationError(
                f"Quantity too small. Minimum: {cls.MIN_POSITION_SIZE}"
            )
        
        return quantity
    
    @classmethod
    def validate_price(cls, price: Optional[float]) -> Optional[float]:
        """Validate price (for limit orders)"""
        if price is None:
            return None
        
        if not isinstance(price, (int, float, Decimal)):
            raise ValidationError("Price must be a number")
        
        price = float(price)
        
        if price <= 0:
            raise ValidationError("Price must be positive")
        
        return price
    
    @classmethod
    def validate_risk_percent(cls, risk_percent: float) -> float:
        """Validate risk percentage"""
        if not isinstance(risk_percent, (int, float)):
            raise ValidationError("Risk percent must be a number")
        
        if risk_percent <= 0 or risk_percent > cls.MAX_RISK_PERCENT:
            raise ValidationError(
                f"Risk percent must be between 0 and {cls.MAX_RISK_PERCENT * 100}%"
            )
        
        return float(risk_percent)
    
    @classmethod
    def validate_stop_loss(cls, entry_price: float, stop_loss: float, side: str) -> float:
        """Validate stop loss level"""
        if stop_loss <= 0:
            raise ValidationError("Stop loss must be positive")
        
        side = side.lower()
        
        # For long positions, stop loss should be below entry
        if side in ['buy', 'long'] and stop_loss >= entry_price:
            raise ValidationError("Stop loss must be below entry price for long positions")
        
        # For short positions, stop loss should be above entry
        if side in ['sell', 'short'] and stop_loss <= entry_price:
            raise ValidationError("Stop loss must be above entry price for short positions")
        
        return float(stop_loss)
    
    @classmethod
    def validate_take_profit(cls, entry_price: float, take_profit: float, side: str) -> float:
        """Validate take profit level"""
        if take_profit <= 0:
            raise ValidationError("Take profit must be positive")
        
        side = side.lower()
        
        # For long positions, take profit should be above entry
        if side in ['buy', 'long'] and take_profit <= entry_price:
            raise ValidationError("Take profit must be above entry price for long positions")
        
        # For short positions, take profit should be below entry
        if side in ['sell', 'short'] and take_profit >= entry_price:
            raise ValidationError("Take profit must be below entry price for short positions")
        
        return float(take_profit)

class StrategyValidator:
    """Validates strategy configurations"""
    
    VALID_INDICATORS = [
        'rsi', 'ema', 'sma', 'macd', 'bollinger', 'atr', 'stochastic',
        'volume', 'obv', 'adx', 'cci', 'mfi'
    ]
    
    @classmethod
    def validate_strategy_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete strategy configuration"""
        required_fields = ['name', 'symbol', 'timeframe']
        
        for field in required_fields:
            if field not in config:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate individual fields
        config['symbol'] = TradingValidator.validate_symbol(config['symbol'])
        config['timeframe'] = TradingValidator.validate_timeframe(config['timeframe'])
        
        # Validate optional fields
        if 'leverage' in config:
            config['leverage'] = TradingValidator.validate_leverage(config['leverage'])
        
        if 'risk_per_trade' in config:
            config['risk_per_trade'] = TradingValidator.validate_risk_percent(
                config['risk_per_trade']
            )
        
        # Validate indicators
        if 'indicators' in config:
            cls._validate_indicators(config['indicators'])
        
        return config
    
    @classmethod
    def _validate_indicators(cls, indicators: Dict[str, Any]):
        """Validate indicator configurations"""
        if not isinstance(indicators, dict):
            raise ValidationError("Indicators must be a dictionary")
        
        for indicator_name, params in indicators.items():
            if indicator_name.lower() not in cls.VALID_INDICATORS:
                raise ValidationError(
                    f"Unknown indicator: {indicator_name}. Valid: {', '.join(cls.VALID_INDICATORS)}"
                )
            
            # Validate indicator parameters
            if isinstance(params, dict):
                if 'period' in params:
                    period = params['period']
                    if not isinstance(period, int) or period < 1:
                        raise ValidationError(
                            f"Invalid period for {indicator_name}: must be positive integer"
                        )

class APIValidator:
    """Validates API inputs"""
    
    @classmethod
    def validate_chat_message(cls, message: str) -> str:
        """Validate chat message"""
        if not message or not isinstance(message, str):
            raise ValidationError("Message must be a non-empty string")
        
        message = message.strip()
        
        if len(message) == 0:
            raise ValidationError("Message cannot be empty")
        
        if len(message) > 10000:
            raise ValidationError("Message too long (max 10000 characters)")
        
        return message
    
    @classmethod
    def validate_date_range(cls, start_date: str, end_date: str) -> tuple:
        """Validate date range"""
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {e}")
        
        if start >= end:
            raise ValidationError("Start date must be before end date")
        
        return start, end
    
    @classmethod
    def validate_api_key(cls, api_key: str) -> str:
        """Validate API key format"""
        if not api_key or not isinstance(api_key, str):
            raise ValidationError("API key must be a non-empty string")
        
        # Basic format check (alphanumeric and common symbols)
        if not re.match(r'^[a-zA-Z0-9_\-]+$', api_key):
            raise ValidationError("Invalid API key format")
        
        return api_key

def validate_order_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to validate complete order parameters
    
    Args:
        params: Dictionary with order parameters
        
    Returns:
        Validated and normalized parameters
    """
    validated = {}
    
    # Required fields
    validated['symbol'] = TradingValidator.validate_symbol(params['symbol'])
    validated['side'] = TradingValidator.validate_order_side(params['side'])
    validated['quantity'] = TradingValidator.validate_quantity(
        params['quantity'], 
        params['symbol']
    )
    
    # Optional fields
    if 'type' in params:
        validated['type'] = TradingValidator.validate_order_type(params['type'])
    
    if 'price' in params:
        validated['price'] = TradingValidator.validate_price(params['price'])
    
    if 'leverage' in params:
        validated['leverage'] = TradingValidator.validate_leverage(params['leverage'])
    
    if 'stop_loss' in params and 'price' in validated:
        validated['stop_loss'] = TradingValidator.validate_stop_loss(
            validated['price'],
            params['stop_loss'],
            validated['side']
        )
    
    if 'take_profit' in params and 'price' in validated:
        validated['take_profit'] = TradingValidator.validate_take_profit(
            validated['price'],
            params['take_profit'],
            validated['side']
        )
    
    return validated

# Example usage and testing
if __name__ == "__main__":
    # Test validation
    try:
        # Valid order
        order = validate_order_params({
            'symbol': 'BTC/USDT:USDT',
            'side': 'buy',
            'quantity': 0.01,
            'type': 'market',
            'leverage': 10
        })
        print("✅ Valid order:", order)
        
        # Invalid symbol
        validate_order_params({
            'symbol': 'INVALID/PAIR',
            'side': 'buy',
            'quantity': 0.01
        })
    except ValidationError as e:
        print(f"❌ Validation error: {e}")
