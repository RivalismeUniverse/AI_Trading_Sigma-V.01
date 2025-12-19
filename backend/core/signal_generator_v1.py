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
        """
        # Safety check for empty data
        if df.empty:
            return {'action': TradeAction.WAIT, 'confidence': 0}

        # Calculate all indicators
        indicators = self.indicators.calculate_all(df)
        
        # Calculate category scores
        scores = self._calculate_category_scores(indicators)
        
        # Aggregate weighted score
        aggregate_score = sum(
            scores[cat] * weight 
            for cat, weight in self.category_weights.items()
        )
        
        # Volatility adjustment
        volatility_factor = self._calculate_volatility_factor(indicators)
        adjusted_score = aggregate_score * volatility_factor
        
        # Market regime filter
        regime_valid, regime_reason = self._check_market_regime(indicators)
        if not regime_valid:
            adjusted_score *= 0.3
        
        # Determine action
        action, confidence = self._score_to_action(adjusted_score)
        
        # Calculate execution parameters
        current_price = df['close'].iloc[-1]
        stop_loss = self._calculate_stop_loss(current_price, indicators, action)
        take_profit = self._calculate_take_profit(current_price, indicators, action)
        
        # Safe Risk Reward Calculation
        denom = abs(stop_loss - current_price)
        risk_reward = abs(take_profit - current_price) / denom if denom > 1e-6 else 0
        
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
        
        logger.info(f"Signal V1: {action} | Price: {current_price} | Conf: {confidence:.3f}")
        
        return signal
    
    def _calculate_category_scores(self, ind: Dict) -> Dict[str, float]:
        """
        Calculate category-based scores [-1, 1]
        Safe from ZeroDivisionError
        """
        scores = {}
        
        # 1. MOMENTUM Score
        momentum_components = []
        rsi_norm = (ind['rsi'] - 50) / 50
        momentum_components.append(-np.tanh(rsi_norm * 2))
        
        stoch_norm = (ind['stoch_k'] - 50) / 50
        momentum_components.append(-np.tanh(stoch_norm * 2))
        
        momentum_components.append(np.tanh(ind['cci'] / 100))
        scores['momentum'] = np.mean(momentum_components)
        
        # 2. TREND Score
        trend_components = []
        trend_components.append(np.tanh(ind['macd_histogram'] / 10))
        
        if ind['ema_9'] > ind['ema_20'] > ind['ema_50']:
            ema_score = 0.8
        elif ind['ema_9'] < ind['ema_20'] < ind['ema_50']:
            ema_score = -0.8
        else:
            ema_score = 0.0
        trend_components.append(ema_score)
        
        adx_strength = min(ind['adx'] / 50, 1.0)
        scores['trend'] = np.mean(trend_components) * adx_strength
        
        # 3. VOLATILITY Score
        bb_position = 0
        # FIX: Check for zero division in BB
        bb_range = ind['bb_upper'] - ind['bb_middle']
        if bb_range > 1e-6:
            bb_position = (ind['current_price'] - ind['bb_middle']) / bb_range
            bb_position = np.clip(bb_position, -1, 1)
        
        vol_score = np.tanh((ind['gk_volatility'] - 0.3) / 0.2)
        scores['volatility'] = -bb_position * 0.7 + vol_score * 0.3
        
        # 4. VOLUME Score
        volume_components = []
        mfi_norm = (ind['mfi'] - 50) / 50
        volume_components.append(np.tanh(mfi_norm * 1.5))
        
        # FIX: Safe VWAP calculation
        vwap_val = ind.get('vwap', 0)
        if vwap_val > 1e-6:
            vwap_diff = (ind['current_price'] - vwap_val) / vwap_val
            vwap_score = np.tanh(vwap_diff * 100)
        else:
            vwap_score = 0.0
        volume_components.append(vwap_score)
        
        scores['volume'] = np.mean(volume_components)
        
        # 5. MEAN REVERSION Score
        mean_rev_components = []
        z_score = ind['z_score']
        if z_score < -2:
            z_reversion = 0.8
        elif z_score > 2:
            z_reversion = -0.8
        else:
            z_reversion = -np.tanh(z_score / 2)
        mean_rev_components.append(z_reversion)
        
        if bb_position < -0.8:
            bb_reversion = 0.6
        elif bb_position > 0.8:
            bb_reversion = -0.6
        else:
            bb_reversion = 0.0
        mean_rev_components.append(bb_reversion)
        scores['mean_reversion'] = np.mean(mean_rev_components)
        
        # 6. PROBABILITY Score
        scores['probability'] = (ind['mc_probability'] - 0.5) * 2
        
        return scores
    
    def _calculate_volatility_factor(self, ind: Dict) -> float:
        gk_vol = ind.get('gk_volatility', 0.3)
        vol_normalized = np.clip((gk_vol - 0.2) / 0.4, 0, 1)
        return 1.0 - (vol_normalized * 0.5)
    
    def _check_market_regime(self, ind: Dict) -> Tuple[bool, str]:
        if ind.get('volume', 0) < 1: # Bypass might give low volume info
            return True, "bypass_mode" # Allow bypass to trade
        if ind.get('gk_volatility', 0) > 0.9:
            return False, "extreme_volatility"
        return True, "regime_ok"
    
    def _score_to_action(self, score: float) -> Tuple[TradeAction, float]:
        confidence = abs(score)
        if score > 0.2:
            return TradeAction.ENTER_LONG, confidence
        elif score < -0.2:
            return TradeAction.ENTER_SHORT, confidence
        return TradeAction.WAIT, confidence
    
    def _calculate_stop_loss(self, current_price: float, ind: Dict, action: TradeAction) -> float:
        atr = ind.get('atr', current_price * 0.01)
        if atr == 0: atr = current_price * 0.005
        stop_dist = atr * 1.5
        return current_price - stop_dist if action == TradeAction.ENTER_LONG else current_price + stop_dist
    
    def _calculate_take_profit(self, current_price: float, ind: Dict, action: TradeAction) -> float:
        atr = ind.get('atr', current_price * 0.01)
        if atr == 0: atr = current_price * 0.005
        tp_dist = atr * 3.0
        return current_price + tp_dist if action == TradeAction.ENTER_LONG else current_price - tp_dist

__all__ = ['SignalGeneratorV1']