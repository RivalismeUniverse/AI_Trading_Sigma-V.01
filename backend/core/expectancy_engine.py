"""
Expectancy Engine - Real Performance Tracking
Tracks actual win rate, payoff ratio, and expectancy from closed trades
Uses empirical data, not fake confidence scores
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from database.db_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ExpectancyEngine:
    """
    Tracks real trading performance for proper Kelly Criterion
    
    Features:
    - Win rate from actual closed trades
    - Payoff ratio (avg_win / avg_loss)
    - Sample size tracking
    - Per-symbol and per-strategy metrics
    - Rolling windows (30/100/500 trades)
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.min_sample_size = 30  # Minimum trades for statistical significance
        
    def get_win_rate(
        self, 
        symbol: Optional[str] = None,
        strategy_id: Optional[int] = None,
        min_trades: int = 30,
        window: Optional[int] = None
    ) -> Optional[float]:
        """
        Get empirical win rate from closed trades
        
        Args:
            symbol: Filter by symbol (None = all)
            strategy_id: Filter by strategy
            min_trades: Minimum trades required
            window: Rolling window (last N trades)
            
        Returns:
            Win rate [0-1] or None if insufficient data
        """
        trades = self._get_closed_trades(symbol, strategy_id, window)
        
        if len(trades) < min_trades:
            logger.debug(f"Insufficient trades for win rate: {len(trades)} < {min_trades}")
            return None
            
        winning_trades = sum(1 for t in trades if t.get('pnl', 0) > 0)
        win_rate = winning_trades / len(trades)
        
        logger.debug(f"Win rate: {win_rate:.2%} ({winning_trades}/{len(trades)} trades)")
        return win_rate
    
    def get_payoff_ratio(
        self,
        symbol: Optional[str] = None,
        strategy_id: Optional[int] = None,
        window: Optional[int] = None
    ) -> Optional[float]:
        """
        Get actual payoff ratio (avg_win / avg_loss)
        
        Returns:
            Payoff ratio or None if insufficient data
        """
        trades = self._get_closed_trades(symbol, strategy_id, window)
        
        winning_pnls = [t['pnl'] for t in trades if t.get('pnl', 0) > 0]
        losing_pnls = [abs(t['pnl']) for t in trades if t.get('pnl', 0) < 0]
        
        if not winning_pnls or not losing_pnls:
            return None
            
        avg_win = np.mean(winning_pnls)
        avg_loss = np.mean(losing_pnls)
        
        if avg_loss == 0:
            return None
            
        payoff_ratio = avg_win / avg_loss
        logger.debug(f"Payoff ratio: {payoff_ratio:.2f} (${avg_win:.2f} / ${avg_loss:.2f})")
        
        return payoff_ratio
    
    def calculate_expectancy(
        self,
        symbol: Optional[str] = None,
        strategy_id: Optional[int] = None,
        window: Optional[int] = None
    ) -> Optional[float]:
        """
        Calculate expectancy per trade
        
        Expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        Returns:
            Expected $ per trade or None
        """
        trades = self._get_closed_trades(symbol, strategy_id, window)
        
        if len(trades) < self.min_sample_size:
            return None
            
        winning_pnls = [t['pnl'] for t in trades if t.get('pnl', 0) > 0]
        losing_pnls = [t['pnl'] for t in trades if t.get('pnl', 0) < 0]
        
        if not trades:
            return None
            
        win_rate = len(winning_pnls) / len(trades)
        loss_rate = len(losing_pnls) / len(trades)
        
        avg_win = np.mean(winning_pnls) if winning_pnls else 0
        avg_loss = abs(np.mean(losing_pnls)) if losing_pnls else 0
        
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        logger.info(f"Expectancy: ${expectancy:.2f} per trade (n={len(trades)})")
        return expectancy
    
    def get_kelly_inputs(
        self,
        symbol: Optional[str] = None,
        strategy_id: Optional[int] = None,
        min_trades: int = 30
    ) -> Optional[Dict]:
        """
        Get proper Kelly Criterion inputs from empirical data
        
        Returns:
            {
                'win_rate': float,
                'payoff_ratio': float,
                'sample_size': int,
                'kelly_fraction': float,
                'confidence_interval': float
            }
            or None if insufficient data
        """
        trades = self._get_closed_trades(symbol, strategy_id)
        
        if len(trades) < min_trades:
            logger.warning(f"Insufficient data for Kelly: {len(trades)} < {min_trades}")
            return None
            
        win_rate = self.get_win_rate(symbol, strategy_id, min_trades=0)
        payoff_ratio = self.get_payoff_ratio(symbol, strategy_id)
        
        if win_rate is None or payoff_ratio is None:
            return None
            
        # Calculate Kelly fraction
        # Kelly = (p * b - q) / b
        # where p = win_rate, q = 1-p, b = payoff_ratio
        kelly = (win_rate * payoff_ratio - (1 - win_rate)) / payoff_ratio
        
        # Confidence interval (larger sample = higher confidence)
        confidence = min(len(trades) / 100, 1.0)  # Max confidence at 100 trades
        
        result = {
            'win_rate': win_rate,
            'payoff_ratio': payoff_ratio,
            'sample_size': len(trades),
            'kelly_fraction': max(0, kelly),  # Never negative
            'confidence_interval': confidence,
            'expectancy': self.calculate_expectancy(symbol, strategy_id)
        }
        
        logger.info(
            f"Kelly inputs: WR={win_rate:.2%}, PR={payoff_ratio:.2f}, "
            f"Kelly={kelly:.3f}, n={len(trades)}"
        )
        
        return result
    
    def get_rolling_metrics(
        self,
        symbol: Optional[str] = None,
        windows: list = [30, 100, 500]
    ) -> Dict:
        """
        Get rolling performance metrics for multiple windows
        
        Returns:
            {
                30: {'win_rate': 0.72, 'expectancy': 15.3, ...},
                100: {...},
                500: {...}
            }
        """
        results = {}
        
        for window in windows:
            trades = self._get_closed_trades(symbol, window=window)
            
            if len(trades) < window:
                continue
                
            results[window] = {
                'win_rate': self.get_win_rate(symbol, window=window, min_trades=0),
                'payoff_ratio': self.get_payoff_ratio(symbol, window=window),
                'expectancy': self.calculate_expectancy(symbol, window=window),
                'sample_size': len(trades)
            }
            
        return results
    
    def detect_degradation(
        self,
        symbol: Optional[str] = None,
        short_window: int = 30,
        long_window: int = 100
    ) -> Dict:
        """
        Detect if recent performance is degrading
        
        Compares short window vs long window
        
        Returns:
            {
                'is_degrading': bool,
                'short_win_rate': float,
                'long_win_rate': float,
                'win_rate_drop': float,
                'expectancy_drop': float
            }
        """
        short_metrics = self._get_closed_trades(symbol, window=short_window)
        long_metrics = self._get_closed_trades(symbol, window=long_window)
        
        if len(short_metrics) < short_window or len(long_metrics) < long_window:
            return {'is_degrading': False, 'reason': 'insufficient_data'}
            
        short_wr = self.get_win_rate(symbol, window=short_window, min_trades=0)
        long_wr = self.get_win_rate(symbol, window=long_window, min_trades=0)
        
        short_exp = self.calculate_expectancy(symbol, window=short_window)
        long_exp = self.calculate_expectancy(symbol, window=long_window)
        
        if short_wr is None or long_wr is None:
            return {'is_degrading': False, 'reason': 'insufficient_data'}
            
        wr_drop = (long_wr - short_wr) / long_wr if long_wr > 0 else 0
        exp_drop = (long_exp - short_exp) / abs(long_exp) if long_exp and long_exp != 0 else 0
        
        # Degradation if win rate drops >20% or expectancy drops >30%
        is_degrading = (wr_drop > 0.20) or (exp_drop > 0.30)
        
        result = {
            'is_degrading': is_degrading,
            'short_win_rate': short_wr,
            'long_win_rate': long_wr,
            'win_rate_drop_pct': wr_drop * 100,
            'short_expectancy': short_exp,
            'long_expectancy': long_exp,
            'expectancy_drop_pct': exp_drop * 100
        }
        
        if is_degrading:
            logger.warning(f"Strategy degradation detected: {result}")
            
        return result
    
    def _get_closed_trades(
        self,
        symbol: Optional[str] = None,
        strategy_id: Optional[int] = None,
        window: Optional[int] = None
    ) -> list:
        """
        Get closed trades with filters
        
        Returns list of trade dicts with 'pnl' field
        """
        # Get all trades from database
        all_trades = self.db.get_trades(limit=1000)
        
        # Filter closed trades (have exit_time and pnl)
        closed_trades = [
            t for t in all_trades 
            if t.get('exit_time') is not None and t.get('pnl') is not None
        ]
        
        # Filter by symbol
        if symbol:
            closed_trades = [t for t in closed_trades if t.get('symbol') == symbol]
            
        # Filter by strategy
        if strategy_id:
            closed_trades = [t for t in closed_trades if t.get('strategy_id') == strategy_id]
            
        # Apply window (last N trades)
        if window:
            closed_trades = closed_trades[-window:]
            
        return closed_trades
    
    def get_performance_summary(self, symbol: Optional[str] = None) -> Dict:
        """
        Get comprehensive performance summary
        
        Returns complete stats for display/reporting
        """
        trades = self._get_closed_trades(symbol)
        
        if not trades:
            return {
                'total_trades': 0,
                'message': 'No closed trades yet'
            }
            
        kelly_inputs = self.get_kelly_inputs(symbol, min_trades=0)
        rolling = self.get_rolling_metrics(symbol)
        degradation = self.detect_degradation(symbol)
        
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades) if trades else 0,
            'payoff_ratio': kelly_inputs.get('payoff_ratio') if kelly_inputs else None,
            'expectancy': kelly_inputs.get('expectancy') if kelly_inputs else None,
            'kelly_fraction': kelly_inputs.get('kelly_fraction') if kelly_inputs else None,
            'rolling_metrics': rolling,
            'degradation': degradation,
            'ready_for_kelly': len(trades) >= self.min_sample_size
        }


__all__ = ['ExpectancyEngine']
