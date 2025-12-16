"""
Risk Manager - Position Sizing & Risk Management
Kelly Criterion + Volatility Adjustment
"""

from typing import Dict, Optional
import numpy as np

from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class RiskManager:
    """
    Advanced risk management system
    Handles position sizing, risk limits, and portfolio management
    """
    
    def __init__(self):
        self.kelly_fraction = settings.KELLY_FRACTION
        self.max_risk_per_trade = settings.MAX_RISK_PER_TRADE
        self.max_daily_loss = settings.MAX_DAILY_LOSS
    
    def calculate_position_size(
        self,
        balance: float,
        risk_pct: float,
        entry_price: float,
        stop_loss_price: float,
        leverage: int = 1,
        confidence: float = 0.6
    ) -> float:
        """
        Calculate optimal position size using Kelly Criterion
        
        Args:
            balance: Account balance
            risk_pct: Risk percentage per trade (e.g., 0.02 for 2%)
            entry_price: Entry price
            stop_loss_price: Stop loss price
            leverage: Leverage to use
            confidence: Signal confidence (0-1)
            
        Returns:
            Position size in base currency
        """
        
        # Base risk amount
        risk_amount = balance * risk_pct
        
        # Calculate price difference (risk per unit)
        price_diff = abs(entry_price - stop_loss_price)
        
        if price_diff == 0:
            logger.warning("Stop loss equals entry price, using minimum size")
            return balance * 0.01 / entry_price  # 1% of balance
        
        # Basic position size
        base_size = risk_amount / price_diff
        
        # Apply Kelly Criterion adjustment
        kelly_size = self._kelly_adjustment(base_size, confidence)
        
        # Apply leverage
        leveraged_size = kelly_size * leverage
        
        # Apply maximum position size limit (10% of balance)
        max_size = (balance * 0.10) / entry_price
        final_size = min(leveraged_size, max_size)
        
        logger.debug(f"Position size calculated: {final_size:.6f}")
        
        return final_size
    
    def _kelly_adjustment(self, base_size: float, confidence: float) -> float:
        """
        Apply Kelly Criterion adjustment
        Kelly Fraction = (p*b - q) / b
        Where p = win probability, q = lose probability, b = win/loss ratio
        """
        
        # Conservative Kelly (use fraction of full Kelly)
        p = confidence  # Win probability
        q = 1 - p  # Lose probability
        b = 2.5  # Assume 2.5:1 reward/risk ratio
        
        kelly = (p * b - q) / b
        
        # Apply Kelly fraction (e.g., 0.25 for conservative)
        adjusted_kelly = kelly * self.kelly_fraction
        
        # Ensure positive and reasonable
        adjusted_kelly = max(0.1, min(adjusted_kelly, 1.0))
        
        return base_size * adjusted_kelly
    
    def validate_risk(
        self,
        position_size: float,
        entry_price: float,
        balance: float,
        open_positions: int = 0
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if trade meets risk requirements
        
        Returns:
            (is_valid, error_message)
        """
        
        # Check if we have too many open positions
        if open_positions >= settings.MAX_OPEN_POSITIONS:
            return False, f"Maximum open positions reached ({settings.MAX_OPEN_POSITIONS})"
        
        # Check position size vs balance
        position_value = position_size * entry_price
        if position_value > balance * 0.1:  # 10% max per position
            return False, "Position size exceeds 10% of balance"
        
        # Check if we have sufficient balance
        required_margin = position_value / settings.DEFAULT_LEVERAGE
        if required_margin > balance:
            return False, "Insufficient balance for position"
        
        return True, None
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        direction: str,
        atr_multiplier: float = 1.5
    ) -> float:
        """
        Calculate stop loss price based on ATR
        
        Args:
            entry_price: Entry price
            atr: Average True Range
            direction: 'long' or 'short'
            atr_multiplier: ATR multiplier for stop distance
            
        Returns:
            Stop loss price
        """
        stop_distance = atr * atr_multiplier
        
        if direction.lower() == 'long':
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance
    
    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss_price: float,
        direction: str,
        risk_reward_ratio: float = 2.5
    ) -> float:
        """
        Calculate take profit price based on risk/reward ratio
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            direction: 'long' or 'short'
            risk_reward_ratio: Desired risk/reward ratio
            
        Returns:
            Take profit price
        """
        stop_distance = abs(entry_price - stop_loss_price)
        target_distance = stop_distance * risk_reward_ratio
        
        if direction.lower() == 'long':
            return entry_price + target_distance
        else:
            return entry_price - target_distance
    
    def calculate_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        initial_stop: float,
        direction: str,
        trailing_pct: float = 0.5
    ) -> float:
        """
        Calculate trailing stop loss
        
        Args:
            entry_price: Original entry price
            current_price: Current market price
            initial_stop: Initial stop loss
            direction: 'long' or 'short'
            trailing_pct: Percentage of profit to trail
            
        Returns:
            New stop loss price
        """
        
        if direction.lower() == 'long':
            # For long positions
            if current_price <= entry_price:
                return initial_stop  # No profit yet
            
            profit = current_price - entry_price
            new_stop = entry_price + (profit * trailing_pct)
            return max(new_stop, initial_stop)
        
        else:
            # For short positions
            if current_price >= entry_price:
                return initial_stop  # No profit yet
            
            profit = entry_price - current_price
            new_stop = entry_price - (profit * trailing_pct)
            return min(new_stop, initial_stop)
    
    def calculate_portfolio_heat(
        self,
        open_positions: list,
        balance: float
    ) -> float:
        """
        Calculate total portfolio heat (total risk exposure)
        
        Args:
            open_positions: List of open position dicts
            balance: Account balance
            
        Returns:
            Portfolio heat as percentage
        """
        total_risk = 0.0
        
        for position in open_positions:
            entry_price = position.get('entry_price', 0)
            stop_loss = position.get('stop_loss', 0)
            size = position.get('position_size', 0)
            
            risk_per_unit = abs(entry_price - stop_loss)
            position_risk = risk_per_unit * size
            total_risk += position_risk
        
        portfolio_heat = (total_risk / balance) * 100 if balance > 0 else 0
        
        return portfolio_heat
    
    def should_reduce_exposure(
        self,
        portfolio_heat: float,
        daily_pnl_pct: float
    ) -> bool:
        """
        Determine if we should reduce exposure
        
        Args:
            portfolio_heat: Current portfolio heat percentage
            daily_pnl_pct: Daily P&L percentage
            
        Returns:
            True if should reduce exposure
        """
        
        # Reduce if portfolio heat too high
        if portfolio_heat > 15.0:  # 15% total risk
            return True
        
        # Reduce if daily loss approaching limit
        if daily_pnl_pct < -3.0:  # -3% daily loss
            return True
        
        return False
    
    def get_risk_metrics(
        self,
        trades: list
    ) -> Dict:
        """
        Calculate risk metrics from trade history
        
        Returns:
            Dictionary with risk metrics
        """
        if not trades:
            return {}
        
        pnls = [t.get('pnl', 0) for t in trades if 'pnl' in t]
        
        if not pnls:
            return {}
        
        returns = np.array(pnls)
        
        metrics = {
            'total_return': sum(pnls),
            'avg_return': np.mean(returns),
            'std_return': np.std(returns),
            'sharpe_ratio': self._calculate_sharpe(returns),
            'max_drawdown': self._calculate_max_drawdown(returns),
            'win_rate': sum(1 for p in pnls if p > 0) / len(pnls) * 100,
            'profit_factor': self._calculate_profit_factor(pnls)
        }
        
        return metrics
    
    def _calculate_sharpe(self, returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe Ratio"""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
        return sharpe
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate Maximum Drawdown"""
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max * 100
        
        return abs(np.min(drawdown)) if len(drawdown) > 0 else 0.0
    
    def _calculate_profit_factor(self, pnls: list) -> float:
        """Calculate Profit Factor"""
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        
        return gross_profit / gross_loss if gross_loss > 0 else 0.0


# Export
__all__ = ['RiskManager']
