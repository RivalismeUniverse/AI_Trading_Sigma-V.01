"""
Trading Constants and Enums
Centralized constants for the trading system
"""

from enum import Enum


# Trading Actions
class TradeAction(str, Enum):
    ENTER_LONG = "ENTER_LONG"
    ENTER_SHORT = "ENTER_SHORT"
    EXIT_LONG = "EXIT_LONG"
    EXIT_SHORT = "EXIT_SHORT"
    WAIT = "WAIT"
    HOLD = "HOLD"


# Order Types
class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    STOP_LOSS_LIMIT = "stop_loss_limit"
    TAKE_PROFIT_LIMIT = "take_profit_limit"


# Order Sides
class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


# Position Sides
class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"
    BOTH = "both"


# Order Status
class OrderStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REJECTED = "rejected"


# Trade Status
class TradeStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELED = "canceled"
    FAILED = "failed"


# Signal Strength
class SignalStrength(str, Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


# Market Condition
class MarketCondition(str, Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    UNCERTAIN = "uncertain"


# Timeframes
TIMEFRAMES = {
    "1m": 60,
    "3m": 180,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "6h": 21600,
    "12h": 43200,
    "1d": 86400
}


# Hackathon Compliance
ALLOWED_SYMBOLS = [
    'ADA/USDT:USDT',
    'SOL/USDT:USDT',
    'LTC/USDT:USDT',
    'DOGE/USDT:USDT',
    'BTC/USDT:USDT',
    'ETH/USDT:USDT',
    'XRP/USDT:USDT',
    'BNB/USDT:USDT'
]

MAX_ALLOWED_LEVERAGE = 20
MIN_TRADES_REQUIRED = 10


# Indicator Thresholds
RSI_OVERSOLD = 30.0
RSI_OVERBOUGHT = 70.0
RSI_STRONG_OVERSOLD = 20.0
RSI_STRONG_OVERBOUGHT = 80.0

STOCH_OVERSOLD = 20.0
STOCH_OVERBOUGHT = 80.0

CCI_OVERSOLD = -100.0
CCI_OVERBOUGHT = 100.0

MFI_OVERSOLD = 20.0
MFI_OVERBOUGHT = 80.0


# Risk Management
DEFAULT_RISK_REWARD_RATIO = 2.5
MIN_RISK_REWARD_RATIO = 1.5
MAX_POSITION_SIZE_PCT = 10.0  # 10% of account
DEFAULT_STOP_LOSS_ATR_MULTIPLIER = 1.5
DEFAULT_TAKE_PROFIT_ATR_MULTIPLIER = 2.5


# Monte Carlo Simulation
MC_DEFAULT_SIMULATIONS = 1000
MC_DEFAULT_HORIZON = 12  # periods
MC_CONFIDENCE_LEVELS = [0.70, 0.90, 0.95]


# Signal Weights (for multi-indicator fusion)
SIGNAL_WEIGHTS = {
    "rsi": 0.15,
    "macd": 0.15,
    "stochastic": 0.10,
    "bollinger": 0.10,
    "ema": 0.10,
    "adx": 0.10,
    "monte_carlo": 0.20,  # High weight for probability-based
    "z_score": 0.05,
    "lr_slope": 0.05
}


# Exchange Specific
EXCHANGE_CONFIGS = {
    "weex": {
        "name": "WEEX",
        "has_perpetual": True,
        "has_margin": True,
        "max_leverage": 125,
        "testnet_url": "https://api-testnet.woo.network",
        "mainnet_url": "https://api.woo.network"
    },
    "binance": {
        "name": "Binance",
        "has_perpetual": True,
        "has_margin": True,
        "max_leverage": 125,
        "testnet_url": "https://testnet.binancefuture.com",
        "mainnet_url": "https://fapi.binance.com"
    }
}


# Performance Metrics
PERFORMANCE_METRICS = [
    "total_return",
    "win_rate",
    "profit_factor",
    "sharpe_ratio",
    "max_drawdown",
    "recovery_factor",
    "calmar_ratio",
    "average_win",
    "average_loss",
    "largest_win",
    "largest_loss",
    "total_trades",
    "winning_trades",
    "losing_trades"
]


# Error Messages
ERROR_MESSAGES = {
    "invalid_symbol": "Symbol not in allowed list for hackathon",
    "leverage_exceeded": "Leverage exceeds maximum allowed (20x)",
    "insufficient_balance": "Insufficient balance for trade",
    "position_limit": "Maximum number of open positions reached",
    "daily_loss_limit": "Daily loss limit exceeded",
    "invalid_strategy": "Invalid or incomplete strategy configuration",
    "exchange_error": "Exchange API error",
    "network_error": "Network connection error",
    "validation_error": "Input validation failed"
}


# Success Messages
SUCCESS_MESSAGES = {
    "trade_opened": "Position opened successfully",
    "trade_closed": "Position closed successfully",
    "strategy_applied": "Strategy applied successfully",
    "bot_started": "Trading bot started",
    "bot_stopped": "Trading bot stopped"
}


# WebSocket Event Types
class WSEventType(str, Enum):
    STATUS_UPDATE = "status_update"
    NEW_TRADE = "new_trade"
    TRADE_CLOSED = "trade_closed"
    BALANCE_UPDATE = "balance_update"
    PERFORMANCE_UPDATE = "performance_update"
    SIGNAL_GENERATED = "signal_generated"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Export all
__all__ = [
    'TradeAction',
    'OrderType',
    'OrderSide',
    'PositionSide',
    'OrderStatus',
    'TradeStatus',
    'SignalStrength',
    'MarketCondition',
    'WSEventType',
    'TIMEFRAMES',
    'ALLOWED_SYMBOLS',
    'MAX_ALLOWED_LEVERAGE',
    'MIN_TRADES_REQUIRED',
    'RSI_OVERSOLD',
    'RSI_OVERBOUGHT',
    'RSI_STRONG_OVERSOLD',
    'RSI_STRONG_OVERBOUGHT',
    'SIGNAL_WEIGHTS',
    'EXCHANGE_CONFIGS',
    'PERFORMANCE_METRICS',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES'
    ]
