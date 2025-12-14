# Trading constants

# Timeframe conversions
TIMEFRAME_SECONDS = {
    '1m': 60,
    '5m': 300,
    '15m': 900,
    '30m': 1800,
    '1h': 3600,
    '4h': 14400,
    '1d': 86400
}

# Trading sessions (UTC hours)
TRADING_SESSIONS = {
    'asian': {'start': 0, 'end': 9, 'volatility_multiplier': 0.8},
    'london': {'start': 8, 'end': 16, 'volatility_multiplier': 1.3},
    'ny': {'start': 13, 'end': 21, 'volatility_multiplier': 1.2},
    'overlap': {'start': 13, 'end': 16, 'volatility_multiplier': 1.5}
}

# Risk management
DEFAULT_RISK_PER_TRADE = 0.02  # 2%
DEFAULT_MAX_DAILY_LOSS = 0.05  # 5%
DEFAULT_MAX_POSITIONS = 3
DEFAULT_STOP_LOSS_ATR_MULTIPLIER = 1.5
DEFAULT_TAKE_PROFIT_ATR_MULTIPLIER = 2.0

# Technical indicators
DEFAULT_RSI_PERIOD = 14
DEFAULT_RSI_OVERSOLD = 30
DEFAULT_RSI_OVERBOUGHT = 70
DEFAULT_EMA_FAST = 8
DEFAULT_EMA_SLOW = 21
DEFAULT_ATR_PERIOD = 14
DEFAULT_VOLUME_THRESHOLD = 1.2

# AI settings
AI_MAX_TOKENS = 2000
AI_TEMPERATURE = 0.7
AI_REVIEW_INTERVAL_HOURS = 6

# Backtesting
MIN_BACKTEST_CANDLES = 500
DEFAULT_BACKTEST_PERIOD = '30d'

# Order types
ORDER_TYPE_MARKET = 'market'
ORDER_TYPE_LIMIT = 'limit'
ORDER_TYPE_STOP_LOSS = 'stop_loss'
ORDER_TYPE_TAKE_PROFIT = 'take_profit'

# Position sides
SIDE_BUY = 'buy'
SIDE_SELL = 'sell'

# Order status
STATUS_OPEN = 'open'
STATUS_CLOSED = 'closed'
STATUS_CANCELLED = 'cancelled'
STATUS_EXPIRED = 'expired'
