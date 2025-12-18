"""
Database Manager - CRUD Operations
Handles all database operations for the trading system
"""

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from database.models import Base, Trade, Strategy, PerformanceMetric, Signal, ComplianceLog, ChatHistory
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseManager:
    """Database operations manager"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    # ========================================================================
    # TRADE OPERATIONS
    # ========================================================================
    
    def save_trade(self, trade_data: Dict) -> int:
        """Save trade to database"""
        session = self.get_session()
        try:
            trade = Trade(**trade_data)
            session.add(trade)
            session.commit()
            trade_id = trade.id
            logger.debug(f"Trade saved: {trade_id}")
            return trade_id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save trade: {e}")
            raise
        finally:
            session.close()
    
    def update_trade(self, trade_id: int, updates: Dict):
        """Update existing trade"""
        session = self.get_session()
        try:
            trade = session.query(Trade).filter(Trade.id == trade_id).first()
            if trade:
                for key, value in updates.items():
                    setattr(trade, key, value)
                session.commit()
                logger.debug(f"Trade updated: {trade_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update trade: {e}")
            raise
        finally:
            session.close()
    
    def get_trades(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get trade history"""
        session = self.get_session()
        try:
            trades = session.query(Trade).order_by(desc(Trade.entry_time)).limit(limit).offset(offset).all()
            return [self._trade_to_dict(t) for t in trades]
        finally:
            session.close()
    
    def get_open_trades(self) -> List[Dict]:
        """Get open trades"""
        session = self.get_session()
        try:
            trades = session.query(Trade).filter(Trade.exit_time.is_(None)).all()
            return [self._trade_to_dict(t) for t in trades]
        finally:
            session.close()
    
    def _trade_to_dict(self, trade: Trade) -> Dict:
        """Convert trade object to dictionary"""
        return {
            'id': trade.id,
            'symbol': trade.symbol,
            'action': trade.action,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'position_size': trade.position_size,
            'leverage': trade.leverage,
            'pnl': trade.pnl,
            'confidence': trade.confidence,
            'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
            'exit_time': trade.exit_time.isoformat() if trade.exit_time else None
        }
    
    # ========================================================================
    # STRATEGY OPERATIONS
    # ========================================================================
    
    def save_strategy(self, strategy_data: Dict) -> int:
        """Save strategy to database"""
        session = self.get_session()
        try:
            strategy = Strategy(**strategy_data)
            session.add(strategy)
            session.commit()
            return strategy.id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save strategy: {e}")
            raise
        finally:
            session.close()
    
    def get_strategy(self, strategy_id: int) -> Optional[Dict]:
        """Get strategy by ID"""
        session = self.get_session()
        try:
            strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
            if strategy:
                return self._strategy_to_dict(strategy)
            return None
        finally:
            session.close()
    
    def get_all_strategies(self) -> List[Dict]:
        """Get all strategies"""
        session = self.get_session()
        try:
            strategies = session.query(Strategy).order_by(desc(Strategy.created_at)).all()
            return [self._strategy_to_dict(s) for s in strategies]
        finally:
            session.close()
    
    def _strategy_to_dict(self, strategy: Strategy) -> Dict:
        """Convert strategy object to dictionary"""
        return {
            'id': strategy.id,
            'name': strategy.name,
            'description': strategy.description,
            'parameters': strategy.parameters,
            'is_active': strategy.is_active,
            'created_at': strategy.created_at.isoformat() if strategy.created_at else None
        }
    
    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================
    
    def save_performance_metric(self, metric_data: Dict):
        """Save performance metric"""
        session = self.get_session()
        try:
            metric = PerformanceMetric(**metric_data)
            session.add(metric)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save metric: {e}")
            raise
        finally:
            session.close()
    
    def get_performance_metrics(self) -> Dict:
        """Get latest performance metrics"""
        session = self.get_session()
        try:
            # Get all trades
            trades = session.query(Trade).all()
            
            total_trades = len(trades)
            winning_trades = sum(1 for t in trades if t.pnl and t.pnl > 0)
            losing_trades = sum(1 for t in trades if t.pnl and t.pnl < 0)
            total_pnl = sum(t.pnl for t in trades if t.pnl)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_pnl': total_pnl,
                'win_rate': win_rate
            }
        finally:
            session.close()
    
    def get_performance_history(self, days: int = 7) -> List[Dict]:
        """Get performance history"""
        session = self.get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            metrics = session.query(PerformanceMetric).filter(
                PerformanceMetric.date >= cutoff
            ).order_by(PerformanceMetric.date).all()
            
            return [{
                'date': m.date.isoformat(),
                'total_pnl': m.total_pnl,
                'win_rate': m.win_rate,
                'balance': m.balance
            } for m in metrics]
        finally:
            session.close()
    
    # ========================================================================
    # SIGNALS
    # ========================================================================
    
    def save_signal(self, signal_data: Dict):
        """Save trading signal"""
        session = self.get_session()
        try:
            signal = Signal(**signal_data)
            session.add(signal)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save signal: {e}")
            raise
        finally:
            session.close()
    
    # ========================================================================
    # COMPLIANCE
    # ========================================================================
    
    def save_compliance_log(self, log_data: Dict):
        """Save compliance log"""
        session = self.get_session()
        try:
            log = ComplianceLog(**log_data)
            session.add(log)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save compliance log: {e}")
            raise
        finally:
            session.close()
    
    def generate_compliance_report(self) -> Dict:
        """Generate compliance report for hackathon"""
        session = self.get_session()
        try:
            trades = session.query(Trade).all()
            violations = session.query(ComplianceLog).filter(
                ComplianceLog.log_type == 'violation'
            ).all()
            
            return {
                'total_trades': len(trades),
                'total_violations': len(violations),
                'compliance_rate': (1 - len(violations) / max(len(trades), 1)) * 100,
                'report_date': datetime.utcnow().isoformat()
            }
        finally:
            session.close()
    
    # ========================================================================
    # CHAT HISTORY
    # ========================================================================
    
    def save_chat_message(self, role: str, message: str, session_id: str = None):
        """Save chat message"""
        session = self.get_session()
        try:
            chat = ChatHistory(role=role, message=message, session_id=session_id)
            session.add(chat)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save chat: {e}")
            raise
        finally:
            session.close()
    
    def get_chat_history(self, session_id: str = None, limit: int = 50) -> List[Dict]:
        """Get chat history"""
        session = self.get_session()
        try:
            query = session.query(ChatHistory)
            if session_id:
                query = query.filter(ChatHistory.session_id == session_id)
            
            messages = query.order_by(ChatHistory.timestamp).limit(limit).all()
            
            return [{
                'role': m.role,
                'message': m.message,
                'timestamp': m.timestamp.isoformat()
            } for m in messages]
        finally:
            session.close()


# Export
__all__ = ['DatabaseManager']
