"""
Scalping Strategy for AI Trading SIGMA
9-phase scalping strategy with advanced indicators
"""
from typing import Dict, Any
import pandas as pd
import numpy as np

from config import settings


class ScalpingStrategy:
    """
    Advanced scalping strategy combining multiple indicators
    with probability-based decision making
    """
    
    def __init__(self):
        self.name = "sigma_scalping"
        self.description = "Advanced 9-phase scalping strategy"
        
        # Strategy weights
        self.weights = {
            'rsi': 0.15,
            'macd': 0.15,
            'bollinger': 0.15,
            'monte_carlo': 0.20,
            'z_score': 0.15,
            'lr_slope': 0.10,
            'volume': 0.05,
            'volatility': 0.05
        }
        
        # Signal thresholds
        self.buy_threshold = 0.65  # 65% confidence needed for buy
        self.sell_threshold = 0.65  # 65% confidence needed for sell
        
        logger.info(f"Scalping strategy '{self.name}' initialized")
    
    def generate_signal(self, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trading signal using 9-phase analysis
        
        Phases:
        1. RSI analysis
        2. MACD crossover
        3. Bollinger Bands position
        4. Monte Carlo probability
        5. Z-Score mean reversion
        6. Linear Regression slope
        7. Volume confirmation
        8. Volatility adjustment
        9. Risk assessment
        
        Returns: Signal dictionary with action, confidence, and reasoning
        """
        try:
            current_price = df['close'].iloc[-1]
            
            # Initialize scores
            long_score = 0.0
            short_score = 0.0
            reasoning = []
            
            # Phase 1: RSI Analysis
            rsi = indicators.get('rsi', 50)
            if rsi < settings.rsi_oversold:
                long_score += self.weights['rsi'] * ((settings.rsi_oversold - rsi) / settings.rsi_oversold)
                reasoning.append(f"RSI oversold: {rsi:.1f}")
            elif rsi > settings.rsi_overbought:
                short_score += self.weights['rsi'] * ((rsi - settings.rsi_overbought) / (100 - settings.rsi_overbought))
                reasoning.append(f"RSI overbought: {rsi:.1f}")
            
            # Phase 2: MACD Analysis
            macd_hist = indicators.get('macd_histogram', 0)
            if macd_hist > 0:
                long_score += self.weights['macd'] * min(abs(macd_hist) / 10, 1.0)
                reasoning.append(f"MACD bullish: {macd_hist:.2f}")
            else:
                short_score += self.weights['macd'] * min(abs(macd_hist) / 10, 1.0)
                reasoning.append(f"MACD bearish: {macd_hist:.2f}")
            
            # Phase 3: Bollinger Bands
            bb_position = indicators.get('bb_position', 0.5)
            if bb_position < 0.2:  # Near lower band
                long_score += self.weights['bollinger'] * ((0.2 - bb_position) / 0.2)
                reasoning.append(f"Near BB lower band: {bb_position:.2f}")
            elif bb_position > 0.8:  # Near upper band
                short_score += self.weights['bollinger'] * ((bb_position - 0.8) / 0.2)
                reasoning.append(f"Near BB upper band: {bb_position:.2f}")
            
            # Phase 4: Monte Carlo Probability
            mc_prob = indicators.get('mc_probability_up', 0.5)
            if mc_prob > 0.6:
                long_score += self.weights['monte_carlo'] * ((mc_prob - 0.5) / 0.5)
                reasoning.append(f"MC probability up: {mc_prob:.1%}")
            elif mc_prob < 0.4:
                short_score += self.weights['monte_carlo'] * ((0.5 - mc_prob) / 0.5)
                reasoning.append(f"MC probability down: {(1-mc_prob):.1%}")
            
            # Phase 5: Z-Score Mean Reversion
            z_score = indicators.get('z_score', 0)
            if z_score < -1.5:  # Oversold
                long_score += self.weights['z_score'] * min(abs(z_score) / 3, 1.0)
                reasoning.append(f"Z-Score oversold: {z_score:.2f}")
            elif z_score > 1.5:  # Overbought
                short_score += self.weights['z_score'] * min(abs(z_score) / 3, 1.0)
                reasoning.append(f"Z-Score overbought: {z_score:.2f}")
            
            # Phase 6: Linear Regression Slope
            lr_slope = indicators.get('lr_slope', 0)
            if lr_slope > 0.001:  # Upward micro-trend
                long_score += self.weights['lr_slope'] * min(lr_slope / 0.01, 1.0)
                reasoning.append(f"Upward micro-trend: {lr_slope:.4f}")
            elif lr_slope < -0.001:  # Downward micro-trend
                short_score += self.weights['lr_slope'] * min(abs(lr_slope) / 0.01, 1.0)
                reasoning.append(f"Downward micro-trend: {lr_slope:.4f}")
            
            # Phase 7: Volume Confirmation
            volume_ratio = indicators.get('volume_ratio', 1)
            if volume_ratio > 1.2:  # High volume
                # High volume confirms the stronger signal
                if long_score > short_score:
                    long_score *= 1.1
                else:
                    short_score *= 1.1
                reasoning.append(f"High volume: {volume_ratio:.1f}x")
            
            # Phase 8: Volatility Adjustment
            volatility = indicators.get('gk_volatility', 0.02)
            if volatility > 0.05:  # High volatility
                # Reduce position in high volatility
                long_score *= 0.8
                short_score *= 0.8
                reasoning.append(f"High volatility: {volatility:.1%}")
            
            # Phase 9: Final Decision
            confidence = max(long_score, short_score)
            
            if long_score > short_score and long_score >= self.buy_threshold:
                action = 'BUY'
                final_confidence = long_score
            elif short_score > long_score and short_score >= self.sell_threshold:
                action = 'SELL'
                final_confidence = short_score
            else:
                action = 'WAIT'
                final_confidence = max(long_score, short_score)
                reasoning.append(f"Confidence below threshold ({self.buy_threshold})")
            
            # Calculate risk parameters
            atr = indicators.get('atr', current_price * 0.01)
            
            if action in ['BUY', 'SELL']:
                # Dynamic stop loss and take profit based on ATR
                if action == 'BUY':
                    stop_loss = current_price - (atr * settings.stop_loss_atr_multiplier)
                    take_profit = current_price + (atr * settings.take_profit_atr_multiplier)
                else:  # SELL
                    stop_loss = current_price + (atr * settings.stop_loss_atr_multiplier)
                    take_profit = current_price - (atr * settings.take_profit_atr_multiplier)
                
                signal = {
                    'action': action,
                    'confidence': float(final_confidence),
                    'reason': ' | '.join(reasoning),
                    'price': float(current_price),
                    'stop_loss': float(stop_loss),
                    'take_profit': float(take_profit),
                    'risk_reward': settings.take_profit_atr_multiplier / settings.stop_loss_atr_multiplier,
                    'indicators': {
                        'rsi': float(rsi),
                        'macd_histogram': float(macd_hist),
                        'mc_probability': float(mc_prob),
                        'z_score': float(z_score),
                        'lr_slope': float(lr_slope)
                    }
                }
            else:
                signal = {
                    'action': 'WAIT',
                    'confidence': float(final_confidence),
                    'reason': ' | '.join(reasoning) if reasoning else 'No clear signal',
                    'price': float(current_price)
                }
            
            return signal
            
        except Exception as e:
            print(f"Error generating scalping signal: {e}")
            return {
                'action': 'WAIT',
                'confidence': 0.0,
                'reason': f'Error: {str(e)}',
                'price': df['close'].iloc[-1] if len(df) > 0 else 0
                                                          }
