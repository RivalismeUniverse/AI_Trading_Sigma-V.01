"""
Database manager for CRUD operations.
Handles all database interactions using SQLAlchemy.
"""
from sqlalchemy import create_engine, desc, and_, or_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from .models import (
    Base, Trade, TradingSignal, Strategy, PerformanceMetric,
    AIInteraction, SystemLog, TradeStatus, TradeSide
)

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations"""
    
    def __init__(self, database_url: str = "sqlite:///trading_bot.db"):
        """
        Initialize database manager
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        logger.info(f"Database initialized: {database_url}")
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    # ===== TRADE OPERATIONS =====
    
    def create_trade(self, trade_data: Dict[str, Any]) -> Trade:
        """Create new trade record"""
        session = self.get_session()
        try:
            trade = Trade(**trade_data)
            session.add(trade)
            session.commit()
            session.refresh(trade)
            logger.info(f"Created trade: {trade.trade_id}")
            return trade
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating trade: {e}")
            raise
        finally:
            session.close()
    
    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """Get trade by ID"""
        session = self.get_session()
        try:
            return session.query(Trade).filter(Trade.trade_id == trade_id).first()
        finally:
            session.close()
    
    def update_trade(self, trade_id: str, updates: Dict[str, Any]) -> Optional[Trade]:
        """Update trade"""
        session = self.get_session()
        try:
            trade = session.query(Trade).filter(Trade.trade_id == trade_id).first()
            if trade:
                for key, value in updates.items():
                    setattr(trade, key, value)
                session.commit()
                session.refresh(trade)
                logger.info(f"Updated trade: {trade_id}")
            return trade
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating trade: {e}")
            raise
        finally:
            session.close()
    
    def get_open_trades(self, symbol: Optional[str] = None) -> List[Trade]:
        """Get all open trades"""
        session = self.get_session()
        try:
            query = session.query(Trade).filter(Trade.status == TradeStatus.OPEN)
            if symbol:
                query = query.filter(Trade.symbol == symbol)
            return query.all()
        finally:
            session.close()
    
    def get_recent_trades(self, limit: int = 50, symbol: Optional[str] = None) -> List[Trade]:
        """Get recent trades"""
        session = self.get_session()
        try:
            query = session.query(Trade).order_by(desc(Trade.created_at))
            if symbol:
                query = query.filter(Trade.symbol == symbol)
            return query.limit(limit).all()
        finally:
            session.close()
    
    def get_trades_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        symbol: Optional[str] = None
    ) -> List[Trade]:
        """Get trades within date range"""
        session = self.get_session()
        try:
            query = session.query(Trade).filter(
                and_(
                    Trade.created_at >= start_date,
                    Trade.created_at <= end_date
                )
            )
            if symbol:
                query = query.filter(Trade.symbol == symbol)
            return query.order_by(desc(Trade.created_at)).all()
        finally:
            session.close()
    
    def get_trades_by_strategy(self, strategy_name: str, limit: int = 100) -> List[Trade]:
        """Get trades for specific strategy"""
        session = self.get_session()
        try:
            return session.query(Trade).filter(
                Trade.strategy_name == strategy_name
            ).order_by(desc(Trade.created_at)).limit(limit).all()
        finally:
            session.close()
    
    # ===== SIGNAL OPERATIONS =====
    
    def create_signal(self, signal_data: Dict[str, Any]) -> TradingSignal:
        """Create new trading signal"""
        session = self.get_session()
        try:
            signal = TradingSignal(**signal_data)
            session.add(signal)
            session.commit()
            session.refresh(signal)
            logger.debug(f"Created signal: {signal.signal_id}")
            return signal
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating signal: {e}")
            raise
        finally:
            session.close()
    
    def get_recent_signals(self, limit: int = 50, symbol: Optional[str] = None) -> List[TradingSignal]:
        """Get recent signals"""
        session = self.get_session()
        try:
            query = session.query(TradingSignal).order_by(desc(TradingSignal.created_at))
            if symbol:
                query = query.filter(TradingSignal.symbol == symbol)
            return query.limit(limit).all()
        finally:
            session.close()
    
    def mark_signal_acted(self, signal_id: str, trade_id: int) -> Optional[TradingSignal]:
        """Mark signal as acted upon"""
        session = self.get_session()
        try:
            signal = session.query(TradingSignal).filter(
                TradingSignal.signal_id == signal_id
            ).first()
            if signal:
                signal.action_taken = True
                signal.trade_id = trade_id
                session.commit()
                session.refresh(signal)
            return signal
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error marking signal: {e}")
            raise
        finally:
            session.close()
    
    # ===== STRATEGY OPERATIONS =====
    
    def create_strategy(self, strategy_data: Dict[str, Any]) -> Strategy:
        """Create new strategy"""
        session = self.get_session()
        try:
            strategy = Strategy(**strategy_data)
            session.add(strategy)
            session.commit()
            session.refresh(strategy)
            logger.info(f"Created strategy: {strategy.name}")
            return strategy
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating strategy: {e}")
            raise
        finally:
            session.close()
    
    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Get strategy by ID"""
        session = self.get_session()
        try:
            return session.query(Strategy).filter(
                Strategy.strategy_id == strategy_id
            ).first()
        finally:
            session.close()
    
    def get_active_strategy(self) -> Optional[Strategy]:
        """Get currently active strategy"""
        session = self.get_session()
        try:
            return session.query(Strategy).filter(
                Strategy.is_active == True
            ).first()
        finally:
            session.close()
    
    def update_strategy(self, strategy_id: str, updates: Dict[str, Any]) -> Optional[Strategy]:
        """Update strategy"""
        session = self.get_session()
        try:
            strategy = session.query(Strategy).filter(
                Strategy.strategy_id == strategy_id
            ).first()
            if strategy:
                for key, value in updates.items():
                    setattr(strategy, key, value)
                session.commit()
                session.refresh(strategy)
                logger.info(f"Updated strategy: {strategy_id}")
            return strategy
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating strategy: {e}")
            raise
        finally:
            session.close()
    
    def activate_strategy(self, strategy_id: str) -> Optional[Strategy]:
        """Activate strategy and deactivate others"""
        session = self.get_session()
        try:
            # Deactivate all strategies
            session.query(Strategy).update({'is_active': False})
            
            # Activate this strategy
            strategy = session.query(Strategy).filter(
                Strategy.strategy_id == strategy_id
            ).first()
            if strategy:
                strategy.is_active = True
                strategy.activated_at = datetime.utcnow()
                session.commit()
                session.refresh(strategy)
                logger.info(f"Activated strategy: {strategy.name}")
            return strategy
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error activating strategy: {e}")
            raise
        finally:
            session.close()
    
    def get_all_strategies(self) -> List[Strategy]:
        """Get all strategies"""
        session = self.get_session()
        try:
            return session.query(Strategy).order_by(desc(Strategy.created_at)).all()
        finally:
            session.close()
    
    # ===== PERFORMANCE METRICS =====
    
    def save_performance_snapshot(self, metrics_data: Dict[str, Any]) -> PerformanceMetric:
        """Save performance metrics snapshot"""
        session = self.get_session()
        try:
            metrics = PerformanceMetric(**metrics_data)
            session.add(metrics)
            session.commit()
            session.refresh(metrics)
            logger.debug("Saved performance snapshot")
            return metrics
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error saving metrics: {e}")
            raise
        finally:
            session.close()
    
    def get_latest_metrics(self) -> Optional[PerformanceMetric]:
        """Get latest performance metrics"""
        session = self.get_session()
        try:
            return session.query(PerformanceMetric).order_by(
                desc(PerformanceMetric.snapshot_time)
            ).first()
        finally:
            session.close()
    
    def get_metrics_history(self, hours: int = 24) -> List[PerformanceMetric]:
        """Get metrics history"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            return session.query(PerformanceMetric).filter(
                PerformanceMetric.snapshot_time >= cutoff
            ).order_by(PerformanceMetric.snapshot_time).all()
        finally:
            session.close()
    
    # ===== AI INTERACTIONS =====
    
    def log_ai_interaction(self, interaction_data: Dict[str, Any]) -> AIInteraction:
        """Log AI interaction"""
        session = self.get_session()
        try:
            interaction = AIInteraction(**interaction_data)
            session.add(interaction)
            session.commit()
            session.refresh(interaction)
            return interaction
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error logging AI interaction: {e}")
            raise
        finally:
            session.close()
    
    def get_ai_interactions(self, limit: int = 50) -> List[AIInteraction]:
        """Get recent AI interactions"""
        session = self.get_session()
        try:
            return session.query(AIInteraction).order_by(
                desc(AIInteraction.created_at)
            ).limit(limit).all()
        finally:
            session.close()
    
    def get_total_ai_cost(self, days: int = 30) -> float:
        """Calculate total AI cost"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            result = session.query(func.sum(AIInteraction.cost)).filter(
                AIInteraction.created_at >= cutoff
            ).scalar()
            return result or 0.0
        finally:
            session.close()
    
    # ===== SYSTEM LOGS =====
    
    def create_system_log(self, log_data: Dict[str, Any]) -> SystemLog:
        """Create system log entry"""
        session = self.get_session()
        try:
            log = SystemLog(**log_data)
            session.add(log)
            session.commit()
            return log
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error creating system log: {e}")
            raise
        finally:
            session.close()
    
    def get_system_logs(
        self, 
        level: Optional[str] = None,
        component: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[SystemLog]:
        """Get system logs"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            query = session.query(SystemLog).filter(SystemLog.created_at >= cutoff)
            
            if level:
                query = query.filter(SystemLog.level == level.upper())
            if component:
                query = query.filter(SystemLog.component == component)
            
            return query.order_by(desc(SystemLog.created_at)).limit(limit).all()
        finally:
            session.close()
    
    # ===== STATISTICS =====
    
    def get_trading_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive trading statistics"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Total trades
            total_trades = session.query(func.count(Trade.id)).filter(
                Trade.created_at >= cutoff
            ).scalar() or 0
            
            # Closed trades
            closed_trades = session.query(Trade).filter(
                and_(
                    Trade.status == TradeStatus.CLOSED,
                    Trade.created_at >= cutoff
                )
            ).all()
            
            # Calculate metrics
            winning_trades = sum(1 for t in closed_trades if t.pnl > 0)
            total_pnl = sum(t.pnl for t in closed_trades)
            win_rate = (winning_trades / len(closed_trades) * 100) if closed_trades else 0
            
            return {
                'total_trades': total_trades,
                'closed_trades': len(closed_trades),
                'winning_trades': winning_trades,
                'losing_trades': len(closed_trades) - winning_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'average_pnl': round(total_pnl / len(closed_trades), 2) if closed_trades else 0,
            }
        finally:
            session.close()
    
    # ===== CLEANUP =====
    
    def cleanup_old_data(self, days: int = 90):
        """Remove old data to prevent database bloat"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Delete old closed trades
            deleted_trades = session.query(Trade).filter(
                and_(
                    Trade.status == TradeStatus.CLOSED,
                    Trade.closed_at < cutoff
                )
            ).delete()
            
            # Delete old signals
            deleted_signals = session.query(TradingSignal).filter(
                TradingSignal.created_at < cutoff
            ).delete()
            
            # Delete old system logs
            deleted_logs = session.query(SystemLog).filter(
                SystemLog.created_at < cutoff
            ).delete()
            
            session.commit()
            
            logger.info(f"Cleanup: removed {deleted_trades} trades, {deleted_signals} signals, {deleted_logs} logs")
            
            return {
                'trades_deleted': deleted_trades,
                'signals_deleted': deleted_signals,
                'logs_deleted': deleted_logs
            }
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error during cleanup: {e}")
            raise
        finally:
            session.close()

# Example usage
if __name__ == "__main__":
    db = DatabaseManager()
    
    # Test trade creation
    trade_data = {
        'trade_id': 'TEST_001',
        'symbol': 'BTC/USDT:USDT',
        'side': TradeSide.LONG,
        'status': TradeStatus.OPEN,
        'quantity': 0.1,
        'leverage': 10,
        'entry_price': 50000,
        'strategy_name': 'Test Strategy'
    }
    
    trade = db.create_trade(trade_data)
    print(f"✅ Created trade: {trade.trade_id}")
    
    # Get statistics
    stats = db.get_trading_statistics(days=30)
    print(f"📊 Statistics: {stats}")
