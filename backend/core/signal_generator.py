"""
Signal Generator - Multi-Indicator Fusion
Generates trading signals by combining 16 indicators with weighted scoring
"""

import pandas as pd
from typing import Dict, Tuple, Optional
from datetime import datetime

from strategies.technical_indicators import TechnicalIndicators
from config import settings
from utils.constants import (
    TradeAction, SignalStrength, MarketCondition,
    RSI_OVERSOLD, RSI_OVERBOUGHT, SIGNAL_WEIGHTS
)
from utils.logger import setup_logger, log_trade_decision

logger = setup_logger(__name__)


class SignalGenerator:
    """
    Generate trading signals using multi-indicator fusion
    Combines 16 indicators with probability-based weighting
    """
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.signal_weights = SIGNAL_WEIGHTS
        self.min_confidence = settings.MIN_CONFIDENCE
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Generate comprehensive trading signal
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading pair symbol
            
        Returns:
            Dictionary with signal details
        """
        
        # Calculate all indicators
        indicators = self.indicators.calculate_all(df)
        
        # Calculate long and short scores
        long_score = self._calculate_long_score(indicators)
        short_score = self._calculate_short_score(indicators)
        
        # Determine action and confidence
        action, confidence = self._determine_action(long_score, short_score)
        
        # Determine signal strength
        strength = self._determine_strength(confidence)
        
        # Determine market condition
        market_condition = self._determine_market_condition(indicators)
        
        # Generate human-readable reasoning
        reasoning = self._generate_reasoning(indicators, action, confidence)
        
        # Calculate risk/reward ratio
        risk_reward = self._calculate_risk_reward(indicators, action)
        
        # Current price
        current_price = df['close'].iloc[-1]
        
        # Create signal object
        signal = {
            'timestamp': datetime.utcnow().isoformat(),
            'symbol': symbol,
            'action': action,
            'confidence': confidence,
            'strength': strength,
            'current_price': current_price,
            'long_score': long_score,
            'short_score': short_score,
            'indicators': indicators,
            'market_condition': market_condition,
            'reasoning': reasoning,
            'risk_reward': risk_reward,
            'stop_loss': self._calculate_stop_loss(current_price, indicators, action),
            'take_profit': self._calculate_take_profit(current_price, indicators, action, risk_reward)
        }
        
        # Log decision for compliance
        if action in [TradeAction.ENTER_LONG, TradeAction.ENTER_SHORT]:
            log_trade_decision(
                symbol=symbol,
                action=action,
                price=current_price,
                indicators=indicators,
                reasoning=reasoning,
                confidence=confidence,
                risk_reward=risk_reward
            )
        
        logger.debug(f"Signal generated: {action} with {confidence:.2f} confidence")
        
        return signal
    
    def _calculate_long_score(self, indicators: Dict[str, float]) -> float:
        """Calculate long (buy) score from indicators"""
        score = 0.0
        
        # RSI - Oversold
        if indicators['rsi'] < RSI_OVERSOLD:
            score += self.signal_weights['rsi'] * 1.0
        elif indicators['rsi'] < 40:
            score += self.signal_weights['rsi'] * 0.5
        
        # MACD - Bullish crossover
        if indicators['macd_histogram'] > 0:
            score += self.signal_weights['macd'] * 1.0
        elif indicators['macd_histogram'] > -5:
            score += self.signal_weights['macd'] * 0.3
        
        # Stochastic - Oversold
        if indicators['stoch_k'] < 20:
            score += self.signal_weights['stochastic'] * 1.0
        elif indicators['stoch_k'] < 40:
            score += self.signal_weights['stochastic'] * 0.5
        
        # Bollinger Bands - Price near lower band
        if indicators['bb_lower'] > 0:
            bb_position = (indicators['bb_middle'] - indicators['bb_lower']) / indicators['bb_width']
            if bb_position < 0.3:
                score += self.signal_weights['bollinger'] * 1.0
        
        # EMA - Bullish alignment
        if indicators['ema_9'] > indicators['ema_20']:
            score += self.signal_weights['ema'] * 0.5
        if indicators['ema_20'] > indicators['ema_50']:
            score += self.signal_weights['ema'] * 0.5
        
        # ADX - Strong trend
        if indicators['adx'] > 25:
            score += self.signal_weights['adx'] * 0.5
        
        # Monte Carlo - High probability of upward movement
        if indicators['mc_probability'] > 0.6:
            score += self.signal_weights['monte_carlo'] * 1.0
        elif indicators['mc_probability'] > 0.5:
            score += self.signal_weights['monte_carlo'] * 0.5
        
        # Z-Score - Oversold
        if indicators['z_score'] < -1.5:
            score += self.signal_weights['z_score'] * 1.0
        elif indicators['z_score'] < -0.5:
            score += self.signal_weights['z_score'] * 0.5
        
        # Linear Regression Slope - Upward trend
        if indicators['lr_slope'] > 0.001:
            score += self.signal_weights['lr_slope'] * 1.0
        elif indicators['lr_slope'] > 0:
            score += self.signal_weights['lr_slope'] * 0.5
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_short_score(self, indicators: Dict[str, float]) -> float:
        """Calculate short (sell) score from indicators"""
        score = 0.0
        
        # RSI - Overbought
        if indicators['rsi'] > RSI_OVERBOUGHT:
            score += self.signal_weights['rsi'] * 1.0
        elif indicators['rsi'] > 60:
            score += self.signal_weights['rsi'] * 0.5
        
        # MACD - Bearish crossover
        if indicators['macd_histogram'] < 0:
            score += self.signal_weights['macd'] * 1.0
        elif indicators['macd_histogram'] < 5:
            score += self.signal_weights['macd'] * 0.3
        
        # Stochastic - Overbought
        if indicators['stoch_k'] > 80:
            score += self.signal_weights['stochastic'] * 1.0
        elif indicators['stoch_k'] > 60:
            score += self.signal_weights['stochastic'] * 0.5
        
        # Bollinger Bands - Price near upper band
        if indicators['bb_upper'] > 0:
            bb_position = (indicators['bb_upper'] - indicators['bb_middle']) / indicators['bb_width']
            if bb_position < 0.3:
                score += self.signal_weights['bollinger'] * 1.0
        
        # EMA - Bearish alignment
        if indicators['ema_9'] < indicators['ema_20']:
            score += self.signal_weights['ema'] * 0.5
        if indicators['ema_20'] < indicators['ema_50']:
            score += self.signal_weights['ema'] * 0.5
        
        # ADX - Strong trend
        if indicators['adx'] > 25:
            score += self.signal_weights['adx'] * 0.5
        
        # Monte Carlo - High probability of downward movement
        if indicators['mc_probability'] < 0.4:
            score += self.signal_weights['monte_carlo'] * 1.0
        elif indicators['mc_probability'] < 0.5:
            score += self.signal_weights['monte_carlo'] * 0.5
        
        # Z-Score - Overbought
        if indicators['z_score'] > 1.5:
            score += self.signal_weights['z_score'] * 1.0
        elif indicators['z_score'] > 0.5:
            score += self.signal_weights['z_score'] * 0.5
        
        # Linear Regression Slope - Downward trend
        if indicators['lr_slope'] < -0.001:
            score += self.signal_weights['lr_slope'] * 1.0
        elif indicators['lr_slope'] < 0:
            score += self.signal_weights['lr_slope'] * 0.5
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _determine_action(self, long_score: float, short_score: float) -> Tuple[TradeAction, float]:
        """Determine trading action based on scores"""
        
        # Calculate confidence as the difference between scores
        if long_score > short_score:
            confidence = long_score
            if confidence >= settings.SIGNAL_LONG_THRESHOLD:
                return TradeAction.ENTER_LONG, confidence
        elif short_score > long_score:
            confidence = short_score
            if confidence >= settings.SIGNAL_SHORT_THRESHOLD:
                return TradeAction.ENTER_SHORT, confidence
        
        # Default to WAIT if no clear signal
        return TradeAction.WAIT, max(long_score, short_score)
    
    def _determine_strength(self, confidence: float) -> SignalStrength:
        """Determine signal strength"""
        if confidence >= 0.8:
            return SignalStrength.STRONG_BUY if confidence > 0 else SignalStrength.STRONG_SELL
        elif confidence >= 0.65:
            return SignalStrength.BUY if confidence > 0 else SignalStrength.SELL
        else:
            return SignalStrength.NEUTRAL
    
    def _determine_market_condition(self, indicators: Dict[str, float]) -> MarketCondition:
        """Determine current market condition"""
        
        # High ADX = Trending
        if indicators['adx'] > 30:
            if indicators['ema_9'] > indicators['ema_50']:
                return MarketCondition.TRENDING_UP
            else:
                return MarketCondition.TRENDING_DOWN
        
        # High volatility
        if indicators['gk_volatility'] > 0.5:
            return MarketCondition.VOLATILE
        
        # Low ADX = Ranging
        if indicators['adx'] < 20:
            return MarketCondition.RANGING
        
        return MarketCondition.UNCERTAIN
    
    def _generate_reasoning(
        self,
        indicators: Dict[str, float],
        action: TradeAction,
        confidence: float
    ) -> str:
        """Generate human-readable reasoning"""
        
        reasons = []
        
        # RSI
        if indicators['rsi'] < 30:
            reasons.append("RSI oversold")
        elif indicators['rsi'] > 70:
            reasons.append("RSI overbought")
        
        # MACD
        if indicators['macd_histogram'] > 5:
            reasons.append("Strong bullish MACD")
        elif indicators['macd_histogram'] < -5:
            reasons.append("Strong bearish MACD")
        
        # Monte Carlo
        if indicators['mc_probability'] > 0.65:
            reasons.append(f"{indicators['mc_probability']*100:.0f}% probability upward")
        elif indicators['mc_probability'] < 0.35:
            reasons.append(f"{(1-indicators['mc_probability'])*100:.0f}% probability downward")
        
        # Z-Score
        if abs(indicators['z_score']) > 2:
            reasons.append("Extreme mean reversion signal")
        
        # Linear Regression
        if abs(indicators['lr_slope']) > 0.002:
            reasons.append("Strong momentum shift")
        
        if not reasons:
            reasons.append("Multiple weak signals")
        
        return " + ".join(reasons)
    
    def _calculate_risk_reward(
        self,
        indicators: Dict[str, float],
        action: TradeAction
    ) -> float:
        """Calculate risk/reward ratio"""
        
        atr = indicators['atr']
        if atr == 0:
            return 2.0  # Default
        
        # Use ATR-based calculation
        stop_distance = atr * settings.DEFAULT_STOP_LOSS_ATR_MULTIPLIER
        target_distance = atr * settings.DEFAULT_TAKE_PROFIT_ATR_MULTIPLIER
        
        return target_distance / stop_distance if stop_distance > 0 else 2.0
    
    def _calculate_stop_loss(
        self,
        current_price: float,
        indicators: Dict[str, float],
        action: TradeAction
    ) -> float:
        """Calculate stop loss price"""
        
        atr = indicators['atr']
        stop_distance = atr * 1.5  # 1.5x ATR
        
        if action == TradeAction.ENTER_LONG:
            return current_price - stop_distance
        elif action == TradeAction.ENTER_SHORT:
            return current_price + stop_distance
        
        return current_price
    
    def _calculate_take_profit(
        self,
        current_price: float,
        indicators: Dict[str, float],
        action: TradeAction,
        risk_reward: float
    ) -> float:
        """Calculate take profit price"""
        
        atr = indicators['atr']
        target_distance = atr * 2.5  # 2.5x ATR
        
        if action == TradeAction.ENTER_LONG:
            return current_price + target_distance
        elif action == TradeAction.ENTER_SHORT:
            return current_price - target_distance
        
        return current_price


# Export
__all__ = ['SignalGenerator']
