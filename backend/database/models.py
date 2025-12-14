"""
Database models for trading system.
Uses SQLAlchemy ORM for PostgreSQL/SQLite.
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    Text, JSON, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class TradeStatus(enum.Enum):
    """Trade status enumeration"""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class TradeSide(enum.Enum):
    """Trade side enumeration"""
    LONG = "long"
    SHORT = "short"

class OrderType(enum.Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class Trade(Base):
    """Trade record model"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Trade details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(TradeSide), nullable=False)
    status = Column(SQLEnum(TradeStatus), nullable=False, default=TradeStatus.PENDING)
    
    # Order details
    order_type = Column(SQLEnum(OrderType), nullable=False, default=OrderType.MARKET)
    quantity = Column(Float, nullable=False)
    leverage = Column(Float, default=1.0)
    
    # Prices
    entry_price = Column(Float)
    exit_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    
    # P&L
    pnl = Column(Float, default=0.0)
    pnl_percent = Column(Float, default=0.0)
    fees = Column(Float, default=0.0)
    
    # Exchange info
    exchange_order_id = Column(String(100))
    exchange_position_id = Column(String(100))
    
    # Strategy info
    strategy_name = Column(String(100), index=True)
    entry_reason = Column(Text)  # Why trade was entered
    exit_reason = Column(Text)   # Why trade was exited
    
    # AI context
    ai_confidence = Column(Float)  # 0-1 confidence score
    ai_analysis = Column(JSON)     # AI analysis data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    opened_at = Column(DateTime)
    closed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    signals = relationship("TradingSignal", back_populates="trade", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_symbol_status', 'symbol', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_strategy_name', 'strategy_name'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'side': self.side.value if self.side else None,
            'status': self.status.value if self.status else None,
            'order_type': self.order_type.value if self.order_type else None,
            'quantity': self.quantity,
            'leverage': self.leverage,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent,
            'fees': self.fees,
            'strategy_name': self.strategy_name,
            'entry_reason': self.entry_reason,
            'exit_reason': self.exit_reason,
            'ai_confidence': self.ai_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
        }

class TradingSignal(Base):
    """Trading signal model"""
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Signal details
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    signal_type = Column(String(20), nullable=False)  # 'entry', 'exit', 'stop_loss', 'take_profit'
    direction = Column(String(10), nullable=False)    # 'long', 'short', 'neutral'
    
    # Signal strength
    confidence = Column(Float, nullable=False)  # 0-1
    strength = Column(Float)  # Signal strength metric
    
    # Price info
    price = Column(Float, nullable=False)
    
    # Indicator values
    indicators = Column(JSON)  # Snapshot of indicators at signal time
    
    # AI analysis
    ai_analysis = Column(Text)
    ai_reasoning = Column(Text)
    
    # Action taken
    action_taken = Column(Boolean, default=False)
    trade_id = Column(Integer, ForeignKey('trades.id'))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    trade = relationship("Trade", back_populates="signals")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'signal_id': self.signal_id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'signal_type': self.signal_type,
            'direction': self.direction,
            'confidence': self.confidence,
            'strength': self.strength,
            'price': self.price,
            'indicators': self.indicators,
            'action_taken': self.action_taken,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class Strategy(Base):
    """Strategy configuration model"""
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Strategy details
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Trading parameters
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    leverage = Column(Float, default=1.0)
    
    # Risk management
    risk_per_trade = Column(Float, default=0.02)  # 2%
    max_positions = Column(Integer, default=3)
    max_daily_loss = Column(Float, default=0.05)  # 5%
    
    # Strategy configuration
    config = Column(JSON, nullable=False)  # Complete strategy config
    
    # Performance tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    
    # Status
    is_active = Column(Boolean, default=False)
    is_backtested = Column(Boolean, default=False)
    backtest_results = Column(JSON)
    
    # AI generation
    generated_by_ai = Column(Boolean, default=False)
    ai_prompt = Column(Text)  # Original user prompt
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'strategy_id': self.strategy_id,
            'name': self.name,
            'description': self.description,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'leverage': self.leverage,
            'risk_per_trade': self.risk_per_trade,
            'max_positions': self.max_positions,
            'config': self.config,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'total_pnl': self.total_pnl,
            'win_rate': self.win_rate,
            'is_active': self.is_active,
            'is_backtested': self.is_backtested,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class PerformanceMetric(Base):
    """Performance metrics snapshot"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Snapshot info
    snapshot_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    period = Column(String(20), nullable=False)  # 'daily', 'hourly', 'realtime'
    
    # Account metrics
    balance = Column(Float, nullable=False)
    equity = Column(Float, nullable=False)
    margin_used = Column(Float, default=0.0)
    margin_available = Column(Float)
    
    # Trading metrics
    total_trades = Column(Integer, default=0)
    open_positions = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    # P&L metrics
    total_pnl = Column(Float, default=0.0)
    daily_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    profit_factor = Column(Float)
    
    # Risk metrics
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    average_win = Column(Float)
    average_loss = Column(Float)
    
    # Strategy breakdown
    strategy_performance = Column(JSON)  # Per-strategy metrics
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'snapshot_time': self.snapshot_time.isoformat() if self.snapshot_time else None,
            'period': self.period,
            'balance': self.balance,
            'equity': self.equity,
            'total_trades': self.total_trades,
            'open_positions': self.open_positions,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_pnl': self.total_pnl,
            'daily_pnl': self.daily_pnl,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
        }

class AIInteraction(Base):
    """AI interaction logs"""
    __tablename__ = 'ai_interactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Interaction details
    interaction_type = Column(String(50), nullable=False)  # 'chat', 'analysis', 'strategy_gen'
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    
    # Context
    context = Column(JSON)  # Additional context data
    
    # Token usage
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cost = Column(Float)  # Estimated cost in USD
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    response_time = Column(Float)  # Response time in seconds
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'interaction_type': self.interaction_type,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'cost': self.cost,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'response_time': self.response_time,
        }

class SystemLog(Base):
    """System logs for debugging and monitoring"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Log details
    level = Column(String(20), nullable=False, index=True)  # 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    component = Column(String(50), nullable=False, index=True)  # Which component logged
    message = Column(Text, nullable=False)
    
    # Additional data
    data = Column(JSON)  # Structured log data
    exception = Column(Text)  # Exception traceback if any
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'level': self.level,
            'component': self.component,
            'message': self.message,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

# Create all tables
def create_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)

# Example usage
if __name__ == "__main__":
    from sqlalchemy import create_engine
    
    # Create SQLite database for testing
    engine = create_engine('sqlite:///trading_bot.db', echo=True)
    create_tables(engine)
    print("✅ Database tables created successfully")
