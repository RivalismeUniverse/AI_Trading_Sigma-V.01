"""
Dynamic Exit Manager - Smart Exit Logic
Beyond simple TP/SL - intelligent exit decisions
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from core.regime_detector import RegimeDetector, MarketRegime
from core.portfolio_risk_manager import PortfolioRiskManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ExitReason(str, Enum):
    """Exit reasons for tracking"""
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"
    TIME_LIMIT = "time_limit"
    REGIME_CHANGE = "regime_change"
    PORTFOLIO_REBALANCE = "portfolio_rebalance"
    BREAKEVEN_MOVE = "breakeven_move"
    THESIS_INVALIDATED = "thesis_invalidated"
    MANUAL = "manual"


class DynamicExitManager:
    """
    Intelligent exit management
    
    Features:
    - Trailing stops based on regime
    - Time-based exits (thesis expiry)
    - Breakeven moves when in profit
    - Regime change exits
    - Portfolio rebalancing exits
    - Partial exit support
    """
    
    def __init__(
        self,
        regime_detector: RegimeDetector,
        portfolio_risk_manager: PortfolioRiskManager
    ):
        self.regime_detector = regime_detector
        self.portfolio_risk = portfolio_risk_manager
        
        # Time limits (minutes)
        self.max_hold_time = {
            MarketRegime.TREND_UP: 240,      # 4 hours in trends
            MarketRegime.TREND_DOWN: 240,
            MarketRegime.RANGE: 120,         # 2 hours in ranges
            MarketRegime.CHOP: 60,           # 1 hour in chop
            MarketRegime.VOLATILE: 30,       # 30 min in volatile
            MarketRegime.UNKNOWN: 180        # 3 hours default
        }
        
        # Trailing stop activation (% profit)
        self.trailing_activation_pct = 0.015  # 1.5% profit
        
        # Breakeven activation (% profit)
        self.breakeven_activation_pct = 0.01  # 1% profit
    
    def should_exit(
        self,
        position: Dict,
        current_price: float,
        current_regime: MarketRegime,
        indicators: Dict,
        open_positions: list,
        balance: float
    ) -> Tuple[bool, ExitReason, Optional[str]]:
        """
        Comprehensive exit check
        
        Args:
            position: Position dict with entry details
            current_price: Current market price
            current_regime: Current regime from detector
            indicators: Current indicator values
            open_positions: All open positions
            balance: Account balance
            
        Returns:
            (should_exit, reason, details)
        """
        entry_price = position['entry_price']
        side = position['side']
        stop_loss = position['stop_loss']
        take_profit = position['take_profit']
        entry_time = position['entry_time']
        entry_regime = position.get('entry_regime', MarketRegime.UNKNOWN)
        
        # Calculate P&L
        if side == 'ENTER_LONG':
            pnl_pct = (current_price - entry_price) / entry_price
        else:  # SHORT
            pnl_pct = (entry_price - current_price) / entry_price
        
        # 1. Stop Loss Check (always first)
        if side == 'ENTER_LONG' and current_price <= stop_loss:
            return True, ExitReason.STOP_LOSS, f"price_{current_price:.2f}_hit_SL_{stop_loss:.2f}"
        elif side == 'ENTER_SHORT' and current_price >= stop_loss:
            return True, ExitReason.STOP_LOSS, f"price_{current_price:.2f}_hit_SL_{stop_loss:.2f}"
        
        # 2. Take Profit Check
        if side == 'ENTER_LONG' and current_price >= take_profit:
            return True, ExitReason.TAKE_PROFIT, f"price_{current_price:.2f}_hit_TP_{take_profit:.2f}"
        elif side == 'ENTER_SHORT' and current_price <= take_profit:
            return True, ExitReason.TAKE_PROFIT, f"price_{current_price:.2f}_hit_TP_{take_profit:.2f}"
        
        # 3. Trailing Stop Check (if in profit)
        if pnl_pct > self.trailing_activation_pct:
            should_exit, details = self._check_trailing_stop(
                position, current_price, pnl_pct, current_regime
            )
            if should_exit:
                return True, ExitReason.TRAILING_STOP, details
        
        # 4. Breakeven Move Check
        if pnl_pct > self.breakeven_activation_pct:
            should_move = self._should_move_to_breakeven(position, current_price, pnl_pct)
            if should_move:
                # Note: This doesn't exit, but signals to update stop loss
                # Actual stop loss update should happen in calling code
                logger.info(f"Position profitable, recommend moving SL to breakeven")
        
        # 5. Time Limit Check
        hold_time = (datetime.utcnow() - entry_time).total_seconds() / 60
        max_time = self.max_hold_time.get(current_regime, 180)
        
        if hold_time > max_time:
            # Only exit on time if not in significant profit
            if pnl_pct < 0.03:  # Less than 3% profit
                return True, ExitReason.TIME_LIMIT, f"held_{hold_time:.0f}min_limit_{max_time}min"
        
        # 6. Regime Change Check
        if entry_regime != MarketRegime.UNKNOWN and current_regime != entry_regime:
            should_exit, details = self._check_regime_change_exit(
                entry_regime, current_regime, pnl_pct
            )
            if should_exit:
                return True, ExitReason.REGIME_CHANGE, details
        
        # 7. Portfolio Rebalancing Check
        should_exit, details = self._check_portfolio_rebalance(
            position, open_positions, balance
        )
        if should_exit:
            return True, ExitReason.PORTFOLIO_REBALANCE, details
        
        # 8. Thesis Invalidation Check
        should_exit, details = self._check_thesis_invalidation(
            position, indicators, current_regime
        )
        if should_exit:
            return True, ExitReason.THESIS_INVALIDATED, details
        
        # No exit conditions met
        return False, None, None
    
    def _check_trailing_stop(
        self,
        position: Dict,
        current_price: float,
        pnl_pct: float,
        regime: MarketRegime
    ) -> Tuple[bool, Optional[str]]:
        """
        Check trailing stop
        
        Tighter trails in ranges/chop, looser in trends
        """
        # Get trailing percentage based on regime
        trailing_pct = {
            MarketRegime.TREND_UP: 0.02,      # 2% trail in trends
            MarketRegime.TREND_DOWN: 0.02,
            MarketRegime.RANGE: 0.015,        # 1.5% in ranges
            MarketRegime.CHOP: 0.01,          # 1% in chop (tight)
            MarketRegime.VOLATILE: 0.025,     # 2.5% in volatile (wider)
            MarketRegime.UNKNOWN: 0.015
        }.get(regime, 0.015)
        
        # Calculate trailing stop level
        entry_price = position['entry_price']
        side = position['side']
        
        if side == 'ENTER_LONG':
            # Trail from highest price reached
            highest_price = position.get('highest_price', entry_price)
            if current_price > highest_price:
                # Update highest (would need to be done in calling code)
                highest_price = current_price
            
            trail_stop = highest_price * (1 - trailing_pct)
            
            if current_price <= trail_stop:
                return True, f"trailing_stop_hit_{current_price:.2f}_below_{trail_stop:.2f}"
        
        else:  # SHORT
            lowest_price = position.get('lowest_price', entry_price)
            if current_price < lowest_price:
                lowest_price = current_price
            
            trail_stop = lowest_price * (1 + trailing_pct)
            
            if current_price >= trail_stop:
                return True, f"trailing_stop_hit_{current_price:.2f}_above_{trail_stop:.2f}"
        
        return False, None
    
    def _should_move_to_breakeven(
        self,
        position: Dict,
        current_price: float,
        pnl_pct: float
    ) -> bool:
        """
        Check if should move stop loss to breakeven
        
        Returns True if position is profitable enough
        """
        # Move to breakeven if:
        # 1. In profit > 1%
        # 2. Stop loss not already at/above breakeven
        
        if pnl_pct < self.breakeven_activation_pct:
            return False
        
        entry_price = position['entry_price']
        current_stop = position['stop_loss']
        side = position['side']
        
        if side == 'ENTER_LONG':
            if current_stop < entry_price:
                return True
        else:  # SHORT
            if current_stop > entry_price:
                return True
        
        return False
    
    def _check_regime_change_exit(
        self,
        entry_regime: MarketRegime,
        current_regime: MarketRegime,
        pnl_pct: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if regime change warrants exit
        
        Exit if regime incompatible with position
        """
        # Don't exit on minor profit
        if pnl_pct > 0.05:  # >5% profit, let it ride
            return False, None
        
        # Exit if entered in trend but now choppy
        if entry_regime in [MarketRegime.TREND_UP, MarketRegime.TREND_DOWN]:
            if current_regime in [MarketRegime.CHOP, MarketRegime.VOLATILE]:
                return True, f"regime_changed_{entry_regime.value}_to_{current_regime.value}"
        
        # Exit if entered in range but now trending opposite
        if entry_regime == MarketRegime.RANGE:
            if current_regime in [MarketRegime.TREND_UP, MarketRegime.TREND_DOWN]:
                # Range strategy likely won't work in trend
                if pnl_pct < 0.02:  # Small profit or loss
                    return True, f"range_to_trend_{current_regime.value}"
        
        return False, None
    
    def _check_portfolio_rebalance(
        self,
        position: Dict,
        open_positions: list,
        balance: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if should exit for portfolio rebalancing
        
        Exit if position contributes to overconcentration
        """
        # Check if portfolio needs hedging
        should_hedge, reason = self.portfolio_risk.should_hedge_portfolio(
            open_positions, balance, current_drawdown_pct=0  # Would need actual drawdown
        )
        
        if should_hedge and "one_sided" in reason:
            # Close positions on the heavy side
            symbol = position['symbol']
            side = position['side']
            
            exposure = self.portfolio_risk.get_portfolio_exposure_breakdown(
                open_positions, balance
            )
            
            # If this position is on the overexposed side
            if side == 'ENTER_LONG' and exposure['net_exposure_pct'] > 50:
                return True, f"portfolio_rebalance_reduce_long_exposure"
            elif side == 'ENTER_SHORT' and exposure['net_exposure_pct'] < -50:
                return True, f"portfolio_rebalance_reduce_short_exposure"
        
        return False, None
    
    def _check_thesis_invalidation(
        self,
        position: Dict,
        indicators: Dict,
        regime: MarketRegime
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if entry thesis is still valid
        
        Exit if key indicators reverse
        """
        entry_reason = position.get('entry_reason', '')
        side = position['side']
        
        # Check key indicators mentioned in entry reason
        if 'RSI' in entry_reason:
            rsi = indicators.get('rsi', 50)
            
            if side == 'ENTER_LONG' and 'oversold' in entry_reason.lower():
                # Long from oversold - exit if now overbought
                if rsi > 70:
                    return True, f"thesis_invalid_RSI_now_overbought_{rsi:.0f}"
            
            elif side == 'ENTER_SHORT' and 'overbought' in entry_reason.lower():
                # Short from overbought - exit if now oversold
                if rsi < 30:
                    return True, f"thesis_invalid_RSI_now_oversold_{rsi:.0f}"
        
        if 'MACD' in entry_reason:
            macd_hist = indicators.get('macd_histogram', 0)
            
            if side == 'ENTER_LONG' and 'bullish' in entry_reason.lower():
                # Long from bullish MACD - exit if bearish cross
                if macd_hist < -10:
                    return True, f"thesis_invalid_MACD_bearish_cross"
            
            elif side == 'ENTER_SHORT' and 'bearish' in entry_reason.lower():
                # Short from bearish MACD - exit if bullish cross
                if macd_hist > 10:
                    return True, f"thesis_invalid_MACD_bullish_cross"
        
        return False, None
    
    def calculate_partial_exit_size(
        self,
        position: Dict,
        current_price: float,
        pnl_pct: float
    ) -> Optional[float]:
        """
        Calculate partial exit size (scaling out)
        
        Returns size to exit (None if no partial exit)
        """
        # Partial exits at profit milestones
        if pnl_pct > 0.04:  # 4% profit - take 50%
            return position['position_size'] * 0.5
        elif pnl_pct > 0.02:  # 2% profit - take 25%
            return position['position_size'] * 0.25
        
        return None


__all__ = ['DynamicExitManager', 'ExitReason']
