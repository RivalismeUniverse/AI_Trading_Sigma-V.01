"""
Trading signal generator.
Generates entry/exit signals based on technical indicators.
"""
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
import pandas as pd
import numpy as np

from backend.strategies.technical_indicators import IndicatorResult

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Signal type enumeration"""
    LONG = "long"
    SHORT = "short"
    CLOSE = "close"
    NONE = "none"

class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_STRONG = 1.0
    STRONG = 0.8
    MODERATE = 0.6
    WEAK = 0.4
    VERY_WEAK = 0.2

class SignalGenerator:
    """Generates trading signals from indicators"""
    
    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize signal generator
        
        Args:
            confidence_threshold: Minimum confidence for signal (0-1)
        """
        self.confidence_threshold = confidence_threshold
        logger.info(f"Signal generator initialized (threshold: {confidence_threshold})")
    
    def generate_signal(
        self,
        indicators: Dict[str, IndicatorResult],
        current_price: float,
        position: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate trading signal from indicators
        
        Args:
            indicators: Dictionary of calculated indicators
            current_price: Current market price
            position: Current position if any
            
        Returns:
            Signal dictionary with action, confidence, reason, etc.
        """
        # If we have a position, check for exit signals first
        if position:
            exit_signal = self._check_exit_signals(indicators, current_price, position)
            if exit_signal['action'] != SignalType.NONE:
                return exit_signal
        
        # Check for entry signals
        long_score = self._calculate_long_score(indicators, current_price)
        short_score = self._calculate_short_score(indicators, current_price)
        
        # Determine action
        if long_score > self.confidence_threshold and long_score > short_score:
            return self._create_long_signal(indicators, current_price, long_score)
        
        elif short_score > self.confidence_threshold and short_score > long_score:
            return self._create_short_signal(indicators, current_price, short_score)
        
        else:
            return self._create_no_signal(long_score, short_score)
    
    def _calculate_long_score(
        self, 
        indicators: Dict[str, IndicatorResult],
        current_price: float
    ) -> float:
        """Calculate bullish signal strength (ENHANCED with scalping indicators)"""
        scores = []
        
        # RSI oversold
        if 'rsi' in indicators:
            rsi = indicators['rsi'].value
            if rsi < 30:
                scores.append(1.0)
            elif rsi < 40:
                scores.append(0.7)
            elif rsi < 50:
                scores.append(0.5)
            else:
                scores.append(0.0)
        
        # ENHANCED: Monte Carlo probability (NEW!)
        if 'mc_probability' in indicators:
            mc_prob = indicators['mc_probability'].value
            if mc_prob > 0.65:  # 65%+ probability of going up
                scores.append(1.0)
            elif mc_prob > 0.55:
                scores.append(0.7)
            else:
                scores.append(0.3)
        
        # ENHANCED: Z-Score mean reversion (NEW!)
        if 'z_score' in indicators:
            z_score = indicators['z_score'].value
            if z_score < -2:  # Strongly oversold
                scores.append(1.0)
            elif z_score < -1:
                scores.append(0.7)
            else:
                scores.append(0.3)
        
        # ENHANCED: Linear Regression Slope (NEW!)
        if 'lr_slope' in indicators:
            slope = indicators['lr_slope'].value
            if slope > 0.5:  # Strong upward micro-trend
                scores.append(0.9)
            elif slope > 0:
                scores.append(0.6)
            else:
                scores.append(0.2)
        
        # MACD bullish
        if 'macd' in indicators and indicators['macd'].metadata:
            histogram = indicators['macd'].metadata.get('histogram', 0)
            if histogram > 0:
                scores.append(0.8)
            else:
                scores.append(0.2)
        
        # Price above EMA (bullish)
        if 'ema_20' in indicators:
            ema = indicators['ema_20'].value
            if current_price > ema:
                distance_pct = ((current_price - ema) / ema) * 100
                if distance_pct < 2:  # Close to EMA = good entry
                    scores.append(0.9)
                else:
                    scores.append(0.6)
            else:
                scores.append(0.3)
        
        # Stochastic oversold
        if 'stochastic' in indicators:
            stoch = indicators['stochastic'].value
            if stoch < 20:
                scores.append(1.0)
            elif stoch < 30:
                scores.append(0.7)
            else:
                scores.append(0.3)
        
        # Volume confirmation
        if 'volume' in indicators and indicators['volume'].metadata:
            volume_ratio = indicators['volume'].metadata.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                scores.append(0.8)
            elif volume_ratio > 1.0:
                scores.append(0.6)
            else:
                scores.append(0.4)
        
        # ADX trend strength
        if 'adx' in indicators:
            adx = indicators['adx'].value
            if adx > 25:
                scores.append(0.8)
            elif adx > 20:
                scores.append(0.6)
            else:
                scores.append(0.4)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_short_score(
        self,
        indicators: Dict[str, IndicatorResult],
        current_price: float
    ) -> float:
        """Calculate bearish signal strength (ENHANCED)"""
        scores = []
        
        # RSI overbought
        if 'rsi' in indicators:
            rsi = indicators['rsi'].value
            if rsi > 70:
                scores.append(1.0)
            elif rsi > 60:
                scores.append(0.7)
            elif rsi > 50:
                scores.append(0.5)
            else:
                scores.append(0.0)
        
        # ENHANCED: Monte Carlo probability
        if 'mc_probability' in indicators:
            mc_prob = indicators['mc_probability'].value
            if mc_prob < 0.35:  # Low probability of going up = bearish
                scores.append(1.0)
            elif mc_prob < 0.45:
                scores.append(0.7)
            else:
                scores.append(0.3)
        
        # ENHANCED: Z-Score mean reversion
        if 'z_score' in indicators:
            z_score = indicators['z_score'].value
            if z_score > 2:  # Strongly overbought
                scores.append(1.0)
            elif z_score > 1:
                scores.append(0.7)
            else:
                scores.append(0.3)
        
        # ENHANCED: Linear Regression Slope
        if 'lr_slope' in indicators:
            slope = indicators['lr_slope'].value
            if slope < -0.5:  # Strong downward micro-trend
                scores.append(0.9)
            elif slope < 0:
                scores.append(0.6)
            else:
                scores.append(0.2)
        
        # MACD bearish
        if 'macd' in indicators and indicators['macd'].metadata:
            histogram = indicators['macd'].metadata.get('histogram', 0)
            if histogram < 0:
                scores.append(0.8)
            else:
                scores.append(0.2)
        
        # Price below EMA (bearish)
        if 'ema_20' in indicators:
            ema = indicators['ema_20'].value
            if current_price < ema:
                distance_pct = ((ema - current_price) / ema) * 100
                if distance_pct < 2:  # Close to EMA = good entry
                    scores.append(0.9)
                else:
                    scores.append(0.6)
            else:
                scores.append(0.3)
        
        # Stochastic overbought
        if 'stochastic' in indicators:
            stoch = indicators['stochastic'].value
            if stoch > 80:
                scores.append(1.0)
            elif stoch > 70:
                scores.append(0.7)
            else:
                scores.append(0.3)
        
        # Volume confirmation
        if 'volume' in indicators and indicators['volume'].metadata:
            volume_ratio = indicators['volume'].metadata.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                scores.append(0.8)
            elif volume_ratio > 1.0:
                scores.append(0.6)
            else:
                scores.append(0.4)
        
        # ADX trend strength
        if 'adx' in indicators:
            adx = indicators['adx'].value
            if adx > 25:
                scores.append(0.8)
            elif adx > 20:
                scores.append(0.6)
            else:
                scores.append(0.4)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _check_exit_signals(
        self,
        indicators: Dict[str, IndicatorResult],
        current_price: float,
        position: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if we should exit current position"""
        side = position.get('side', 'long')
        entry_price = position.get('entry_price', current_price)
        
        # Calculate current P&L
        if side == 'long':
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - current_price) / entry_price) * 100
        
        # Exit reasons
        exit_reasons = []
        
        # 1. RSI extreme reversal
        if 'rsi' in indicators:
            rsi = indicators['rsi'].value
            if side == 'long' and rsi > 75:
                exit_reasons.append("RSI overbought")
            elif side == 'short' and rsi < 25:
                exit_reasons.append("RSI oversold")
        
        # 2. MACD reversal
        if 'macd' in indicators and indicators['macd'].metadata:
            histogram = indicators['macd'].metadata.get('histogram', 0)
            if side == 'long' and histogram < 0:
                exit_reasons.append("MACD bearish crossover")
            elif side == 'short' and histogram > 0:
                exit_reasons.append("MACD bullish crossover")
        
        # 3. Take quick profit if significant gain
        if pnl_pct > 3:  # 3% profit
            exit_reasons.append(f"Quick profit target ({pnl_pct:.2f}%)")
        
        # 4. EMA crossover
        if 'ema_9' in indicators and 'ema_20' in indicators:
            ema_9 = indicators['ema_9'].value
            ema_20 = indicators['ema_20'].value
            
            if side == 'long' and ema_9 < ema_20:
                exit_reasons.append("EMA bearish crossover")
            elif side == 'short' and ema_9 > ema_20:
                exit_reasons.append("EMA bullish crossover")
        
        if exit_reasons:
            return {
                'action': SignalType.CLOSE.value,
                'confidence': 0.8,
                'reason': ', '.join(exit_reasons),
                'pnl_percent': pnl_pct
            }
        
        return self._create_no_signal(0, 0)
    
    def _create_long_signal(
        self,
        indicators: Dict[str, IndicatorResult],
        current_price: float,
        confidence: float
    ) -> Dict[str, Any]:
        """Create long entry signal"""
        # Calculate stop loss and take profit
        atr = indicators.get('atr')
        atr_value = atr.value if atr else current_price * 0.02
        
        stop_loss = current_price - (atr_value * 1.5)
        take_profit = current_price + (atr_value * 2.5)
        
        # Build reason
        reasons = []
        if 'rsi' in indicators and indicators['rsi'].value < 40:
            reasons.append(f"RSI oversold ({indicators['rsi'].value:.1f})")
        if 'macd' in indicators and indicators['macd'].metadata.get('histogram', 0) > 0:
            reasons.append("MACD bullish")
        if 'stochastic' in indicators and indicators['stochastic'].value < 30:
            reasons.append("Stochastic oversold")
        
        return {
            'action': SignalType.LONG.value,
            'confidence': confidence,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': ', '.join(reasons) if reasons else "Multiple bullish indicators",
            'risk_reward_ratio': (take_profit - current_price) / (current_price - stop_loss)
        }
    
    def _create_short_signal(
        self,
        indicators: Dict[str, IndicatorResult],
        current_price: float,
        confidence: float
    ) -> Dict[str, Any]:
        """Create short entry signal"""
        # Calculate stop loss and take profit
        atr = indicators.get('atr')
        atr_value = atr.value if atr else current_price * 0.02
        
        stop_loss = current_price + (atr_value * 1.5)
        take_profit = current_price - (atr_value * 2.5)
        
        # Build reason
        reasons = []
        if 'rsi' in indicators and indicators['rsi'].value > 60:
            reasons.append(f"RSI overbought ({indicators['rsi'].value:.1f})")
        if 'macd' in indicators and indicators['macd'].metadata.get('histogram', 0) < 0:
            reasons.append("MACD bearish")
        if 'stochastic' in indicators and indicators['stochastic'].value > 70:
            reasons.append("Stochastic overbought")
        
        return {
            'action': SignalType.SHORT.value,
            'confidence': confidence,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': ', '.join(reasons) if reasons else "Multiple bearish indicators",
            'risk_reward_ratio': (current_price - take_profit) / (stop_loss - current_price)
        }
    
    def _create_no_signal(self, long_score: float, short_score: float) -> Dict[str, Any]:
        """Create no-action signal"""
        return {
            'action': SignalType.NONE.value,
            'confidence': 0.0,
            'reason': f"No clear signal (Long: {long_score:.2f}, Short: {short_score:.2f})",
            'long_score': long_score,
            'short_score': short_score
        }
    
    def backtest_signals(
        self,
        ohlcv: pd.DataFrame,
        indicators_series: List[Dict[str, IndicatorResult]]
    ) -> List[Dict[str, Any]]:
        """
        Backtest signal generation on historical data
        
        Args:
            ohlcv: Historical OHLCV data
            indicators_series: List of indicator dictionaries for each candle
            
        Returns:
            List of generated signals
        """
        signals = []
        
        for i in range(len(ohlcv)):
            if i >= len(indicators_series):
                break
            
            current_price = ohlcv.iloc[i]['close']
            indicators = indicators_series[i]
            
            signal = self.generate_signal(indicators, current_price, None)
            
            if signal['action'] != SignalType.NONE.value:
                signal['timestamp'] = ohlcv.iloc[i]['timestamp']
                signal['price'] = current_price
                signals.append(signal)
        
        return signals

# Example usage
if __name__ == "__main__":
    from backend.strategies.technical_indicators import IndicatorCalculator
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='5T')
    prices = np.cumsum(np.random.randn(100)) + 100
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices + np.random.rand(100),
        'low': prices - np.random.rand(100),
        'close': prices,
        'volume': np.random.rand(100) * 1000
    })
    
    # Calculate indicators
    calculator = IndicatorCalculator()
    indicators = calculator.calculate_all(df)
    
    # Generate signal
    generator = SignalGenerator(confidence_threshold=0.6)
    signal = generator.generate_signal(indicators, prices[-1], None)
    
    print(f"📊 Signal: {signal['action'].upper()}")
    print(f"   Confidence: {signal['confidence']:.2f}")
    print(f"   Reason: {signal['reason']}")
