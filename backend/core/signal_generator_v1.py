"""
Signal Generator V1 - CORE ENGINE (Probabilistic)
Category-based probabilistic fusion for real market execution
This is the MAIN trading brain - optimized for actual P&L
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from datetime import datetime

from strategies.technical_indicators import TechnicalIndicators
from config import settings
from utils.constants import TradeAction
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SignalGeneratorV1:
    """
    Core probabilistic signal generator
    Uses category-based scoring with continuous values [-1, 1]
    Market-aware with volatility adjustment
    """
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        
        # Category weights (must sum to 1.0)
        self.category_weights = {
            'momentum': 0.25,      # RSI, Stochastic, CCI
            'trend': 0.20,         # MACD, EMA crossovers
            'volatility': 0.15,    # BB, ATR
            'volume': 0.10,        # OBV, MFI, VWAP
            'mean_reversion': 0.20, # Z-score, BB position
            'probability': 0.10    # Monte Carlo
        }
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Generate probabilistic trading signal
        
        Returns signal with continuous confidence [-1, 1]
        Negative = short bias, Positive = long bias
        """
        
        # Calculate all indicators
        indicators = self.indicators.calculate_all(df)
        
        # Calculate category scores
        scores = self._calculate_category_scores(indicators)
        
        # Aggregate weighted score
        aggregate_score = sum(
            scores[cat] * weight 
            for cat, weight in self.category_weights.items()
        )
        
        # Volatility adjustment (reduce confidence in high vol)
        volatility_factor = self._calculate_volatility_factor(indicators)
        adjusted_score = aggregate_score * volatility_factor
        
        # Market regime filter
        regime_valid, regime_reason = self._check_market_regime(indicators)
        if not regime_valid:
            adjusted_score *= 0.3  # Reduce confidence significantly
        
        # Determine action
        action, confidence = self._score_to_action(adjusted_score)
        
        # Calculate execution parameters
        current_price = df['close'].iloc[-1]
        stop_loss = self._calculate_stop_loss(current_price, indicators, action)
        take_profit = self._calculate_take_profit(current_price, indicators, action)
        risk_reward = abs(take_profit - current_price) / abs(stop_loss - current_price) if stop_loss != current_price else 0
        
        # Build signal
        signal = {
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'action': action,
            'confidence': confidence,
            'raw_score': aggregate_score,
            'adjusted_score': adjusted_score,
            'current_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_reward': risk_reward,
            'volatility_factor': volatility_factor,
            'regime_valid': regime_valid,
            'regime_reason': regime_reason,
            'category_scores': scores,
            'indicators': indicators
        }
        
        logger.debug(f"Signal V1: {action} | Score: {adjusted_score:.3f} | Conf: {confidence:.3f}")
        
        return signal
    
    def _calculate_category_scores(self, ind: Dict) -> Dict[str, float]:
        """
        Calculate category-based scores [-1, 1]
        Negative = bearish, Positive = bullish
        """
        scores = {}
        
        # 1. MOMENTUM Score
        momentum_components = []
        
        # RSI: normalize to [-1, 1]
        rsi_norm = (ind['rsi'] - 50) / 50  # RSI 0→-1, 50→0, 100→1
        rsi_score = -np.tanh(rsi_norm * 2)  # Inverse: low RSI = bullish
        momentum_components.append(rsi_score)
        
        # Stochastic
        stoch_norm = (ind['stoch_k'] - 50) / 50
        stoch_score = -np.tanh(stoch_norm * 2)
        momentum_components.append(stoch_score)
        
        # CCI: normalize
        cci_score = np.tanh(ind['cci'] / 100)
        momentum_components.append(cci_score)
        
        scores['momentum'] = np.mean(momentum_components)
        
        # 2. TREND Score
        trend_components = []
        
        # MACD histogram
        macd_score = np.tanh(ind['macd_histogram'] / 10)
        trend_components.append(macd_score)
        
        # EMA alignment
        if ind['ema_9'] > ind['ema_20'] > ind['ema_50']:
            ema_score = 0.8
        elif ind['ema_9'] < ind['ema_20'] < ind['ema_50']:
            ema_score = -0.8
        else:
            ema_score = 0.0
        trend_components.append(ema_score)
        
        # ADX strength modifier
        adx_strength = min(ind['adx'] / 50, 1.0)  # 0-1
        
        scores['trend'] = np.mean(trend_components) * adx_strength
        
        # 3. VOLATILITY Score (expansion/contraction)
        bb_position = 0
        if ind['bb_width'] > 0:
            # Where is price in BB? -1=lower, 0=middle, 1=upper
            bb_position = (ind['current_price'] - ind['bb_middle']) / (ind['bb_upper'] - ind['bb_middle']) * 2
            bb_position = np.clip(bb_position, -1, 1)
        
        # Low volatility = mean reversion bias
        # High volatility = trend following bias
        vol_score = np.tanh((ind['gk_volatility'] - 0.3) / 0.2)  # Normalized around 0.3
        
        scores['volatility'] = -bb_position * 0.7 + vol_score * 0.3
        
        # 4. VOLUME Score
        volume_components = []
        
        # MFI
        mfi_norm = (ind['mfi'] - 50) / 50
        mfi_score = np.tanh(mfi_norm * 1.5)
        volume_components.append(mfi_score)
        
        # VWAP position
        vwap_diff = (ind['current_price'] - ind['vwap']) / ind['vwap']
        vwap_score = np.tanh(vwap_diff * 100)
        volume_components.append(vwap_score)
        
        scores['volume'] = np.mean(volume_components)
        
        # 5. MEAN REVERSION Score
        mean_rev_components = []
        
        # Z-Score: extreme values = reversion opportunity
        z_score = ind['z_score']
        if z_score < -2:  # Oversold
            z_reversion = 0.8
        elif z_score > 2:  # Overbought
            z_reversion = -0.8
        else:
            z_reversion = -np.tanh(z_score / 2)
        mean_rev_components.append(z_reversion)
        
        # BB position extreme
        if bb_position < -0.8:  # Near lower band
            bb_reversion = 0.6
        elif bb_position > 0.8:  # Near upper band
            bb_reversion = -0.6
        else:
            bb_reversion = 0.0
        mean_rev_components.append(bb_reversion)
        
        scores['mean_reversion'] = np.mean(mean_rev_components)
        
        # 6. PROBABILITY Score (Monte Carlo)
        mc_prob = ind['mc_probability']
        # Convert probability to score: 0.5→0, 0→-1, 1→1
        prob_score = (mc_prob - 0.5) * 2
        scores['probability'] = prob_score
        
        return scores
    
    def _calculate_volatility_factor(self, ind: Dict) -> float:
        """
        Calculate volatility adjustment factor [0.5, 1.0]
        High volatility = lower confidence
        """
        gk_vol = ind['gk_volatility']
        
        # Normalize volatility (typical range 0.2-0.6)
        vol_normalized = (gk_vol - 0.2) / 0.4
        vol_normalized = np.clip(vol_normalized, 0, 1)
        
        # Factor: 1.0 at low vol, 0.5 at high vol
        factor = 1.0 - (vol_normalized * 0.5)
        
        return factor
    
    def _check_market_regime(self, ind: Dict) -> Tuple[bool, str]:
        """
        Check if market regime is favorable for trading
        Returns (is_valid, reason)
        """
        
        # Check 1: Extremely low volume (dead market)
        if ind['volume'] < 100:  # Adjust threshold as needed
            return False, "low_volume"
        
        # Check 2: Extreme volatility spike (potential manipulation)
        if ind['gk_volatility'] > 0.8:
            return False, "extreme_volatility"
        
        # Check 3: Conflicting signals (uncertainty)
        if ind['adx'] < 15:  # Very weak trend
            if abs(ind['z_score']) < 0.5:  # And not at extremes
                return False, "ranging_uncertain"
        
        return True, "regime_ok"
    
    def _score_to_action(self, score: float) -> Tuple[TradeAction, float]:
        """
        Convert continuous score to action + confidence
        
        Score ranges:
        > 0.4: Strong Long
        > 0.2: Long
        -0.2 to 0.2: Wait
        < -0.2: Short
        < -0.4: Strong Short
        """
        
        confidence = abs(score)
        
        if score > 0.4:
            return TradeAction.ENTER_LONG, confidence
        elif score > 0.2:
            return TradeAction.ENTER_LONG, confidence
        elif score < -0.4:
            return TradeAction.ENTER_SHORT, confidence
        elif score < -0.2:
            return TradeAction.ENTER_SHORT, confidence
        else:
            return TradeAction.WAIT, confidence
    
    def _calculate_stop_loss(
        self,
        current_price: float,
        ind: Dict,
        action: TradeAction
    ) -> float:
        """ATR-based stop loss with volatility scaling"""
        
        atr = ind['atr']
        gk_vol = ind['gk_volatility']
        
        # Dynamic multiplier based on volatility
        # High vol = wider stop
        vol_multiplier = 1.0 + (gk_vol / 0.4)  # Range: 1.0-2.0
        stop_distance = atr * 1.5 * vol_multiplier
        
        if action == TradeAction.ENTER_LONG:
            return current_price - stop_distance
        elif action == TradeAction.ENTER_SHORT:
            return current_price + stop_distance
        
        return current_price
    
    def _calculate_take_profit(
        self,
        current_price: float,
        ind: Dict,
        action: TradeAction
    ) -> float:
        """Dynamic take profit based on expected move"""
        
        atr = ind['atr']
        mc_expected = ind['mc_expected_price']
        
        # Use MC expected price if available and reasonable
        if action == TradeAction.ENTER_LONG:
            if mc_expected > current_price * 1.005:  # At least 0.5% profit
                return mc_expected
            else:
                return current_price + (atr * 2.5)
        elif action == TradeAction.ENTER_SHORT:
            if mc_expected < current_price * 0.995:
                return mc_expected
            else:
                return current_price - (atr * 2.5)
        
        return current_price


# Export
__all__ = ['SignalGeneratorV1']
