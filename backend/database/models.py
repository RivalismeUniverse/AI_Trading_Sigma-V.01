"""
Database Models - SQLAlchemy ORM Models
6 tables for complete data tracking
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Trade(Base):
    """Trade records"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)  # ENTER_LONG, ENTER_SHORT, etc.
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    position_size = Column(Float, nullable=False)
    leverage = Column(Integer, default=1)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    exit_reason = Column(String(50), nullable=True)
    indicators = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Trade {self.id}: {self.symbol} {self.action} @ {self.entry_price}>"


class Strategy(Base):
    """Trading strategies"""
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    performance_metrics = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Strategy {self.id}: {self.name}>"


class PerformanceMetric(Base):
    """Daily performance metrics"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    balance = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<Metric {self.date}: {self.total_pnl}>"


class Signal(Base):
    """Trading signals generated"""
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    indicators = Column(JSON, nullable=False)
    reasoning = Column(Text, nullable=True)
    was_executed = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Signal {self.symbol} {self.action} @ {self.timestamp}>"


class ComplianceLog(Base):
    """Compliance and safety logs"""
    __tablename__ = 'compliance_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    log_type = Column(String(50), nullable=False)  # ai_decision, violation, etc.
    symbol = Column(String(50), nullable=True)
    data = Column(JSON, nullable=False)
    severity = Column(String(20), default='info')
    
    def __repr__(self):
        return f"<ComplianceLog {self.log_type} @ {self.timestamp}>"


class ChatHistory(Base):
    """AI chat conversation history"""
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    role = Column(String(20), nullable=False)  # user or assistant
    message = Column(Text, nullable=False)
    session_id = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<Chat {self.role} @ {self.timestamp}>"


# Export
__all__ = [
    'Base',
    'Trade',
    'Strategy',
    'PerformanceMetric',
    'Signal',
    'ComplianceLog',
    'ChatHistory'
    ]
