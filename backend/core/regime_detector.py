"""
Regime Detector - Market State Classification
Classifies market into: TREND_UP, TREND_DOWN, RANGE, CHOP
Uses multiple indicators for robust detection
"""
from typing import Dict, Tuple
from enum import Enum
import pandas as pd
import numpy as np
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MarketRegime(str, Enum):
    """Market regime types"""
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    RANGE = "range"
    CHOP = "chop"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class RegimeDetector:
    """
    Detects current market regime for adaptive risk management
    
    Uses:
    - ADX for trend strength
    - ATR for volatility
    - EMA alignment for trend direction
    - Price action patterns
    - Volume profile
    """
    
    def __init__(self):
        # Thresholds
        self.adx_trend_threshold = 25
        self.adx_strong_trend_threshold = 35
        self.adx_range_threshold = 20
        
        self.volatility_high_threshold = 0.5
        self.volatility_extreme_threshold = 0.8
        
    def detect(self, df: pd.DataFrame, indicators: Dict) -> Dict:
        """
        Detect current market regime
        
        Args:
            df: OHLCV DataFrame
            indicators: Pre-calculated indicators dict
            
        Returns:
            {
                'regime': MarketRegime,
                'confidence': float,
                'details': dict,
                'risk_multiplier': float
            }
        """
        # Extract key indicators
        adx = indicators.get('adx', 20)
        gk_volatility = indicators.get('gk_volatility', 0.3)
        ema_9 = indicators.get('ema_9', 0)
        ema_20 = indicators.get('ema_20', 0)
        ema_50 = indicators.get('ema_50', 0)
        ema_200 = indicators.get('ema_200', 0)
        atr = indicators.get('atr', 0)
        current_price = indicators.get('current_price', df['close'].iloc[-1])
        
        # Detect regime
        regime, confidence, details = self._classify_regime(
            adx, gk_volatility, ema_9, ema_20, ema_50, ema_200, 
            current_price, atr, df
        )
        
        # Calculate risk multiplier
        risk_multiplier = self._calculate_risk_multiplier(regime, adx, gk_volatility)
        
        result = {
            'regime': regime,
            'confidence': confidence,
            'details': details,
            'risk_multiplier': risk_multiplier,
            'trend_strength': adx,
            'volatility': gk_volatility
        }
        
        logger.info(f"Regime: {regime.value} (conf={confidence:.2f}, risk_mult={risk_multiplier:.2f})")
        
        return result
    
    def _classify_regime(
        self,
        adx: float,
        volatility: float,
        ema_9: float,
        ema_20: float,
        ema_50: float,
        ema_200: float,
        price: float,
        atr: float,
        df: pd.DataFrame
    ) -> Tuple[MarketRegime, float, Dict]:
        """
        Classify market regime using multiple criteria
        
        Returns:
            (regime, confidence, details)
        """
        details = {}
        
        # Check for extreme volatility first
        if volatility > self.volatility_extreme_threshold:
            return MarketRegime.VOLATILE, 0.9, {
                'reason': 'extreme_volatility',
                'volatility': volatility
            }
        
        # Trend detection
        is_strong_trend = adx > self.adx_strong_trend_threshold
        is_trend = adx > self.adx_trend_threshold
        is_ranging = adx < self.adx_range_threshold
        
        # EMA alignment
        bullish_alignment = (ema_9 > ema_20 > ema_50 > ema_200)
        bearish_alignment = (ema_9 < ema_20 < ema_50 < ema_200)
        
        # Price vs EMA
        above_ema_50 = price > ema_50
        below_ema_50 = price < ema_50
        
        # Recent price action
        recent_closes = df['close'].iloc[-20:]
        price_std = recent_closes.std()
        price_mean = recent_closes.mean()
        
        # Decision tree
        if is_strong_trend:
            if bullish_alignment and above_ema_50:
                confidence = min(adx / 50, 1.0)
                return MarketRegime.TREND_UP, confidence, {
                    'reason': 'strong_uptrend',
                    'adx': adx,
                    'ema_alignment': 'bullish'
                }
            elif bearish_alignment and below_ema_50:
                confidence = min(adx / 50, 1.0)
                return MarketRegime.TREND_DOWN, confidence, {
                    'reason': 'strong_downtrend',
                    'adx': adx,
                    'ema_alignment': 'bearish'
                }
        
        elif is_trend:
            if above_ema_50:
                confidence = adx / 40
                return MarketRegime.TREND_UP, confidence, {
                    'reason': 'uptrend',
                    'adx': adx
                }
            elif below_ema_50:
                confidence = adx / 40
                return MarketRegime.TREND_DOWN, confidence, {
                    'reason': 'downtrend',
                    'adx': adx
                }
        
        elif is_ranging:
            # Check if really ranging or just choppy
            if price_std / price_mean < 0.02:  # Low volatility range
                confidence = 1.0 - (adx / 20)
                return MarketRegime.RANGE, confidence, {
                    'reason': 'low_volatility_range',
                    'adx': adx,
                    'price_std': price_std
                }
            else:
                # Choppy market
                confidence = 0.7
                return MarketRegime.CHOP, confidence, {
                    'reason': 'choppy_low_adx',
                    'adx': adx,
                    'price_std': price_std
                }
        
        # Default: CHOP if unclear
        return MarketRegime.CHOP, 0.5, {
            'reason': 'unclear_regime',
            'adx': adx,
            'volatility': volatility
        }
    
    def _calculate_risk_multiplier(
        self,
        regime: MarketRegime,
        adx: float,
        volatility: float
    ) -> float:
        """
        Calculate risk multiplier based on regime
        
        Returns:
            Multiplier for position sizing (0.3 to 1.5)
        """
        base_multipliers = {
            MarketRegime.TREND_UP: 1.3,      # Increase size in uptrends
            MarketRegime.TREND_DOWN: 1.3,    # Increase size in downtrends
            MarketRegime.RANGE: 0.8,         # Reduce in ranges
            MarketRegime.CHOP: 0.4,          # Minimal in chop
            MarketRegime.VOLATILE: 0.3,      # Very small in extreme vol
            MarketRegime.UNKNOWN: 0.7        # Conservative if unknown
        }
        
        multiplier = base_multipliers.get(regime, 0.7)
        
        # Adjust by volatility
        if volatility > self.volatility_high_threshold:
            multiplier *= 0.7  # Reduce in high volatility
        
        # Adjust by trend strength (for trends)
        if regime in [MarketRegime.TREND_UP, MarketRegime.TREND_DOWN]:
            if adx > 40:
                multiplier *= 1.1  # Boost for very strong trends
        
        # Clamp
        multiplier = max(0.3, min(multiplier, 1.5))
        
        return multiplier
    
    def should_trade(self, regime_result: Dict) -> Tuple[bool, str]:
        """
        Determine if conditions are good for trading
        
        Returns:
            (should_trade, reason)
        """
        regime = regime_result['regime']
        confidence = regime_result['confidence']
        volatility = regime_result['volatility']
        
        # Don't trade in extreme volatility
        if regime == MarketRegime.VOLATILE:
            return False, "extreme_volatility"
        
        # Be cautious in chop
        if regime == MarketRegime.CHOP and confidence > 0.6:
            return False, "choppy_market"
        
        # Don't trade if very uncertain
        if confidence < 0.3:
            return False, "low_confidence_regime"
        
        # Don't trade in extreme vol even if not labeled VOLATILE
        if volatility > 0.9:
            return False, "volatility_too_high"
        
        return True, "regime_suitable"
    
    def get_regime_strategy_preference(self, regime: MarketRegime) -> Dict:
        """
        Get strategy preferences for current regime
        
        Returns recommended strategy adjustments
        """
        preferences = {
            MarketRegime.TREND_UP: {
                'strategy_type': 'trend_following',
                'prefer_long': True,
                'prefer_short': False,
                'indicators': ['EMA', 'MACD', 'ADX'],
                'avoid_indicators': ['BB_extremes', 'Z_score'],
                'holding_time': 'medium_to_long'
            },
            MarketRegime.TREND_DOWN: {
                'strategy_type': 'trend_following',
                'prefer_long': False,
                'prefer_short': True,
                'indicators': ['EMA', 'MACD', 'ADX'],
                'avoid_indicators': ['BB_extremes', 'Z_score'],
                'holding_time': 'medium_to_long'
            },
            MarketRegime.RANGE: {
                'strategy_type': 'mean_reversion',
                'prefer_long': None,  # Both sides OK
                'prefer_short': None,
                'indicators': ['BB', 'RSI', 'Z_score', 'Stochastic'],
                'avoid_indicators': ['EMA_cross', 'MACD_trend'],
                'holding_time': 'short'
            },
            MarketRegime.CHOP: {
                'strategy_type': 'avoid',
                'prefer_long': False,
                'prefer_short': False,
                'indicators': [],
                'avoid_indicators': ['all'],
                'holding_time': 'none'
            },
            MarketRegime.VOLATILE: {
                'strategy_type': 'avoid_or_scalp',
                'prefer_long': None,
                'prefer_short': None,
                'indicators': ['ATR', 'BB_width'],
                'avoid_indicators': ['slow_indicators'],
                'holding_time': 'very_short'
            }
        }
        
        return preferences.get(regime, {})


__all__ = ['RegimeDetector', 'MarketRegime']
