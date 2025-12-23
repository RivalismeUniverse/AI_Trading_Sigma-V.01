"""
Enhanced Risk Manager - PROPER Kelly Criterion + Regime Awareness
Replaces old risk_manager.py with proper implementation

Key improvements:
1. Uses REAL win rate from expectancy engine (not fake confidence)
2. Only uses Kelly if sample size > 30 trades
3. Regime-aware position sizing
4. Returns 0 if expectancy <= 0
5. No forced minimum Kelly
"""
from typing import Dict, Optional
import numpy as np
from config import settings
from core.expectancy_engine import ExpectancyEngine
from core.regime_detector import RegimeDetector, MarketRegime
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EnhancedRiskManager:
    """
    Production-grade risk manager with proper Kelly Criterion
    
    Features:
    - Empirical Kelly (from real trade data)
    - Regime-aware sizing
    - Volatility adjustment
    - Portfolio heat management
    - Conservative fractional Kelly (0.25x default)
    """
    
    def __init__(
        self,
        expectancy_engine: ExpectancyEngine,
        regime_detector: RegimeDetector,
        kelly_fraction: float = 0.25
    ):
        self.expectancy = expectancy_engine
        self.regime_detector = regime_detector
        self.kelly_fraction = kelly_fraction
        
        self.max_risk_per_trade = settings.MAX_RISK_PER_TRADE
        self.max_daily_loss = settings.MAX_DAILY_LOSS
        
    def calculate_position_size(
        self,
        balance: float,
        entry_price: float,
        stop_loss_price: float,
        leverage: int,
        symbol: str,
        regime_result: Dict,
        confidence: Optional[float] = None
    ) -> float:
        """
        Calculate optimal position size using proper Kelly + regime adjustment
        
        Args:
            balance: Account balance
            entry_price: Entry price
            stop_loss_price: Stop loss price
            leverage: Leverage to use
            symbol: Trading symbol
            regime_result: From regime_detector.detect()
            confidence: V1 confidence (used only if no trade history)
            
        Returns:
            Position size in base currency (0 if shouldn't trade)
        """
        # Step 1: Get Kelly inputs from real data
        kelly_inputs = self.expectancy.get_kelly_inputs(
            symbol=symbol,
            min_trades=30
        )
        
        # Step 2: Calculate base size
        if kelly_inputs and kelly_inputs['sample_size'] >= 30:
            # Use empirical Kelly (PROPER method)
            base_size = self._kelly_size(
                balance, entry_price, stop_loss_price,
                kelly_inputs, leverage
            )
            method = "empirical_kelly"
        else:
            # Not enough data - use conservative exploration size
            base_size = self._exploration_size(
                balance, entry_price, stop_loss_price,
                leverage, confidence
            )
            method = "exploration"
        
        # Step 3: Check if expectancy is positive
        if kelly_inputs and kelly_inputs.get('expectancy', 0) <= 0:
            logger.warning(f"Negative expectancy for {symbol}, sizing = 0")
            return 0.0
        
        # Step 4: Apply regime adjustment
        regime_multiplier = regime_result.get('risk_multiplier', 0.7)
        adjusted_size = base_size * regime_multiplier
        
        # Step 5: Apply volatility adjustment
        volatility = regime_result.get('volatility', 0.3)
        vol_penalty = self._volatility_penalty(volatility)
        adjusted_size *= vol_penalty
        
        # Step 6: Apply hard limits
        max_size = self._calculate_max_size(balance, entry_price, leverage)
        final_size = min(adjusted_size, max_size)
        
        # Ensure positive
        final_size = max(0.0, final_size)
        
        logger.info(
            f"Position size: {final_size:.6f} | Method: {method} | "
            f"Regime mult: {regime_multiplier:.2f} | Vol penalty: {vol_penalty:.2f}"
        )
        
        return final_size
    
    def _kelly_size(
        self,
        balance: float,
        entry_price: float,
        stop_loss_price: float,
        kelly_inputs: Dict,
        leverage: int
    ) -> float:
        """
        Calculate size using empirical Kelly Criterion
        
        Kelly formula: f = (p*b - q) / b
        where:
            p = win_rate (from real trades)
            q = 1 - p
            b = payoff_ratio (avg_win / avg_loss)
        """
        win_rate = kelly_inputs['win_rate']
        payoff_ratio = kelly_inputs['payoff_ratio']
        kelly_fraction_raw = kelly_inputs['kelly_fraction']
        
        # Apply conservative Kelly fraction (0.25x default)
        kelly_adjusted = kelly_fraction_raw * self.kelly_fraction
        
        # CRITICAL: If Kelly <= 0, DON'T TRADE
        if kelly_adjusted <= 0:
            logger.warning("Kelly <= 0, no edge detected")
            return 0.0
        
        # Calculate risk amount based on Kelly
        risk_amount = balance * kelly_adjusted
        
        # Calculate position size from risk
        price_diff = abs(entry_price - stop_loss_price)
        if price_diff == 0:
            return 0.0
            
        position_size = (risk_amount / price_diff) * leverage
        
        logger.debug(
            f"Kelly sizing: WR={win_rate:.2%}, PR={payoff_ratio:.2f}, "
            f"Kelly={kelly_adjusted:.3f}, Size={position_size:.6f}"
        )
        
        return position_size
    
    def _exploration_size(
        self,
        balance: float,
        entry_price: float,
        stop_loss_price: float,
        leverage: int,
        confidence: Optional[float]
    ) -> float:
        """
        Conservative size for exploration phase (< 30 trades)
        
        Uses small fixed percentage (0.5-1%) for data gathering
        """
        # Base exploration risk: 0.5%
        base_exploration_risk = 0.005
        
        # Can increase slightly with V1 confidence (but stay conservative)
        if confidence and confidence > 0.7:
            exploration_risk = base_exploration_risk * 1.5  # Max 0.75%
        else:
        exploration_risk = base_exploration_risk
        
        risk_amount = balance * exploration_risk
        
        price_diff = abs(entry_price - stop_loss_price)
        if price_diff == 0:
            return 0.0
            
        position_size = (risk_amount / price_diff) * leverage
        
        logger.debug(f"Exploration sizing: {exploration_risk:.2%} risk = {position_size:.6f}")
        
        return position_size
    
    def _volatility_penalty(self, volatility: float) -> float:
        """
        Apply penalty for high volatility
        
        Returns multiplier [0.3 - 1.0]
        """
        if volatility < 0.3:
            return 1.0  # Normal volatility
        elif volatility < 0.5:
            return 0.85  # Slightly high
        elif volatility < 0.7:
            return 0.65  # High
        elif volatility < 0.9:
            return 0.45  # Very high
        else:
            return 0.3  # Extreme
    
    def _calculate_max_size(
        self,
        balance: float,
        entry_price: float,
        leverage: int
    ) -> float:
        """
        Calculate maximum allowed position size
        
        Hard limit: 10% of balance (notional value)
        """
        max_notional = balance * 0.10
        max_size = max_notional / entry_price
        
        return max_size
    
    def validate_risk(
        self,
        position_size: float,
        entry_price: float,
        balance: float,
        open_positions: int = 0,
        leverage: int = 1
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if trade meets risk requirements
        
        Returns:
            (is_valid, error_message)
        """
        # Check max open positions
        if open_positions >= settings.MAX_OPEN_POSITIONS:
            return False, f"Maximum open positions reached ({settings.MAX_OPEN_POSITIONS})"
        
        # Check position size vs balance
        position_value = position_size * entry_price
        
        if position_value > balance * 0.1:
            return False, "Position size exceeds 10% of balance"
        
        # Check required margin
        required_margin = position_value / leverage
        
        if required_margin > balance:
            return False, "Insufficient balance for position"
        
        # Check if position size is too small
        if position_size == 0:
            return False, "Position size is zero (no edge or insufficient data)"
        
        return True, None
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        direction: str,
        regime: MarketRegime,
        atr_multiplier: float = 1.5
    ) -> float:
        """
        Calculate stop loss price with regime adjustment
        
        Wider stops in volatile regimes, tighter in ranges
        """
        # Adjust ATR multiplier by regime
        if regime == MarketRegime.VOLATILE:
            atr_multiplier *= 1.5  # Wider stops
        elif regime == MarketRegime.TREND_UP or regime == MarketRegime.TREND_DOWN:
            atr_multiplier *= 1.2  # Slightly wider in trends
        elif regime == MarketRegime.RANGE:
            atr_multiplier *= 0.9  # Tighter in ranges
        elif regime == MarketRegime.CHOP:
            atr_multiplier *= 0.8  # Very tight in chop
        
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
        regime: MarketRegime,
        risk_reward_ratio: float = 2.5
    ) -> float:
        """
        Calculate take profit price with regime adjustment
        
        Higher targets in trends, lower in ranges
        """
        # Adjust RR by regime
        if regime == MarketRegime.TREND_UP or regime == MarketRegime.TREND_DOWN:
            risk_reward_ratio *= 1.2  # Higher targets in trends
        elif regime == MarketRegime.RANGE:
            risk_reward_ratio *= 0.8  # Lower targets in ranges
        elif regime == MarketRegime.CHOP:
            risk_reward_ratio *= 0.7  # Quick exits in chop
        
        stop_distance = abs(entry_price - stop_loss_price)
        target_distance = stop_distance * risk_reward_ratio
        
        if direction.lower() == 'long':
            return entry_price + target_distance
        else:
            return entry_price - target_distance
    
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
        daily_pnl_pct: float,
        regime: MarketRegime
    ) -> tuple[bool, str]:
        """
        Determine if should reduce exposure
        
        Returns:
            (should_reduce, reason)
        """
        # Reduce if portfolio heat too high
        if portfolio_heat > 15.0:
            return True, f"portfolio_heat_high_{portfolio_heat:.1f}%"
        
        # Reduce if daily loss approaching limit
        if daily_pnl_pct < -3.0:
            return True, f"daily_loss_{daily_pnl_pct:.1f}%"
        
        # Reduce in choppy/volatile markets with existing positions
        if regime in [MarketRegime.CHOP, MarketRegime.VOLATILE] and portfolio_heat > 8.0:
            return True, f"unfavorable_regime_{regime.value}"
        
        return False, "exposure_ok"
    
    def get_risk_metrics(self, trades: list) -> Dict:
        """
        Calculate risk metrics from trade history
        
        Returns comprehensive risk analytics
        """
        if not trades:
            return {
                'total_trades': 0,
                'message': 'No trades available'
            }
        
        pnls = [t.get('pnl', 0) for t in trades if 'pnl' in t]
        
        if not pnls:
            return {
                'total_trades': len(trades),
                'message': 'No P&L data available'
            }
        
        returns = np.array(pnls)
        
        # Basic metrics
        total_return = sum(pnls)
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Sharpe ratio
        sharpe = self._calculate_sharpe(returns)
        
        # Max drawdown
        max_dd = self._calculate_max_drawdown(returns)
        
        # Win rate
        winning_trades = sum(1 for p in pnls if p > 0)
        win_rate = winning_trades / len(pnls) * 100 if pnls else 0
        
        # Profit factor
        profit_factor = self._calculate_profit_factor(pnls)
        
        return {
            'total_trades': len(trades),
            'total_return': total_return,
            'avg_return': avg_return,
            'std_return': std_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'profit_factor': profit_factor
        }
    
    def _calculate_sharpe(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.02
    ) -> float:
        """Calculate Sharpe Ratio"""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        
        return sharpe
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate Maximum Drawdown"""
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max)
        
        max_dd = abs(np.min(drawdown)) if len(drawdown) > 0 else 0.0
        
        return max_dd
    
    def _calculate_profit_factor(self, pnls: list) -> float:
        """Calculate Profit Factor"""
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        
        return gross_profit / gross_loss if gross_loss > 0 else 0.0


__all__ = ['EnhancedRiskManager']
