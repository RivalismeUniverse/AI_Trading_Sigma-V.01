"""
Signal Validator V2 - COMPLIANCE & EXPLANATION LAYER
Rule-based validator for explainability and hackathon compliance
Works as confirmation/explanation layer on top of V1
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime

from utils.constants import (
    TradeAction, SignalStrength, MarketCondition,
    RSI_OVERSOLD, RSI_OVERBOUGHT
)
from utils.logger import setup_logger, log_trade_decision

logger = setup_logger(__name__)


class SignalValidatorV2:
    """
    Rule-based signal validator and explainer
    Provides human-readable reasoning and compliance checks
    """
    
    def __init__(self):
        self.validation_rules = {
            'min_confidence': 0.4,
            'min_indicators_agree': 3,
            'max_conflicting_signals': 2
        }
    
    def validate_and_explain(
        self,
        v1_signal: Dict,
        indicators: Dict
    ) -> Dict:
        """
        Validate V1 signal and generate explanation
        
        Returns enhanced signal with:
        - validation_status
        - signal_strength
        - market_condition
        - reasoning (human-readable)
        - supporting_indicators
        - conflicting_indicators
        """
        
        # Analyze indicators using rules
        analysis = self._analyze_indicators(indicators)
        
        # Validate signal consistency
        is_valid, validation_reason = self._validate_consistency(
            v1_signal,
            analysis
        )
        
        # Determine signal strength
        strength = self._determine_strength(
            v1_signal['confidence'],
            analysis['supporting_count']
        )
        
        # Determine market condition
        market_condition = self._determine_market_condition(indicators)
        
        # Generate human-readable reasoning
        reasoning = self._generate_reasoning(
            v1_signal['action'],
            analysis,
            indicators
        )
        
        # Calculate confirmation score (how many rules agree)
        confirmation_score = self._calculate_confirmation_score(
            v1_signal['action'],
            analysis
        )
        
        # Enhanced signal
        validated_signal = {
            **v1_signal,  # Keep all V1 data
            'validation': {
                'is_valid': is_valid,
                'validation_reason': validation_reason,
                'confirmation_score': confirmation_score,
                'signal_strength': strength,
                'market_condition': market_condition
            },
            'explanation': {
                'reasoning': reasoning,
                'supporting_indicators': analysis['supporting'],
                'conflicting_indicators': analysis['conflicting'],
                'neutral_indicators': analysis['neutral']
            }
        }
        
        # Log for compliance if actionable
        if v1_signal['action'] in [TradeAction.ENTER_LONG, TradeAction.ENTER_SHORT]:
            if is_valid:
                self._log_compliance(validated_signal)
        
        logger.info(f"Signal validated: {is_valid} | Strength: {strength} | Confirmation: {confirmation_score:.1f}%")
        
        return validated_signal
    
    def _analyze_indicators(self, ind: Dict) -> Dict:
        """
        Analyze indicators using clear rules
        Returns lists of supporting, conflicting, neutral
        """
        
        supporting = []
        conflicting = []
        neutral = []
        
        # RSI Analysis
        if ind['rsi'] < 30:
            supporting.append(('RSI', 'oversold', 'long', ind['rsi']))
        elif ind['rsi'] > 70:
            supporting.append(('RSI', 'overbought', 'short', ind['rsi']))
        elif 40 < ind['rsi'] < 60:
            neutral.append(('RSI', 'neutral', ind['rsi']))
        
        # MACD Analysis
        if ind['macd_histogram'] > 5:
            supporting.append(('MACD', 'bullish_cross', 'long', ind['macd_histogram']))
        elif ind['macd_histogram'] < -5:
            supporting.append(('MACD', 'bearish_cross', 'short', ind['macd_histogram']))
        else:
            neutral.append(('MACD', 'weak', ind['macd_histogram']))
        
        # Stochastic Analysis
        if ind['stoch_k'] < 20:
            supporting.append(('Stochastic', 'oversold', 'long', ind['stoch_k']))
        elif ind['stoch_k'] > 80:
            supporting.append(('Stochastic', 'overbought', 'short', ind['stoch_k']))
        
        # Bollinger Bands
        current_price = ind.get('current_price', 0)
        if current_price < ind['bb_lower'] * 1.005:  # Near lower band
            supporting.append(('BB', 'lower_band', 'long', current_price))
        elif current_price > ind['bb_upper'] * 0.995:  # Near upper band
            supporting.append(('BB', 'upper_band', 'short', current_price))
        
        # EMA Trend
        if ind['ema_9'] > ind['ema_20'] > ind['ema_50']:
            supporting.append(('EMA', 'bullish_alignment', 'long', 0))
        elif ind['ema_9'] < ind['ema_20'] < ind['ema_50']:
            supporting.append(('EMA', 'bearish_alignment', 'short', 0))
        
        # ADX Strength
        if ind['adx'] > 25:
            supporting.append(('ADX', 'strong_trend', 'both', ind['adx']))
        elif ind['adx'] < 15:
            conflicting.append(('ADX', 'weak_trend', 'wait', ind['adx']))
        
        # Monte Carlo Probability
        if ind['mc_probability'] > 0.65:
            supporting.append(('MonteCarlo', 'high_prob_up', 'long', ind['mc_probability']))
        elif ind['mc_probability'] < 0.35:
            supporting.append(('MonteCarlo', 'high_prob_down', 'short', ind['mc_probability']))
        
        # Z-Score Mean Reversion
        if ind['z_score'] < -2:
            supporting.append(('ZScore', 'extreme_oversold', 'long', ind['z_score']))
        elif ind['z_score'] > 2:
            supporting.append(('ZScore', 'extreme_overbought', 'short', ind['z_score']))
        
        # Linear Regression Slope
        if ind['lr_slope'] > 0.002:
            supporting.append(('LRSlope', 'strong_uptrend', 'long', ind['lr_slope']))
        elif ind['lr_slope'] < -0.002:
            supporting.append(('LRSlope', 'strong_downtrend', 'short', ind['lr_slope']))
        
        return {
            'supporting': supporting,
            'conflicting': conflicting,
            'neutral': neutral,
            'supporting_count': len(supporting)
        }
    
    def _validate_consistency(
        self,
        v1_signal: Dict,
        analysis: Dict
    ) -> Tuple[bool, str]:
        """
        Validate if V1 signal is consistent with rule-based analysis
        """
        
        action = v1_signal['action']
        confidence = v1_signal['confidence']
        
        # If V1 says WAIT, always respect it
        if action == TradeAction.WAIT:
            return True, "v1_wait_respected"
        
        # Check minimum confidence
        if confidence < self.validation_rules['min_confidence']:
            return False, f"low_confidence_{confidence:.2f}"
        
        # Count supporting vs conflicting
        direction = 'long' if action == TradeAction.ENTER_LONG else 'short'
        
        supporting_count = sum(
            1 for ind in analysis['supporting']
            if ind[2] == direction or ind[2] == 'both'
        )
        
        conflicting_count = len(analysis['conflicting'])
        
        # Check if enough indicators support
        if supporting_count < self.validation_rules['min_indicators_agree']:
            return False, f"insufficient_support_{supporting_count}"
        
        # Check if too many conflicts
        if conflicting_count > self.validation_rules['max_conflicting_signals']:
            return False, f"too_many_conflicts_{conflicting_count}"
        
        return True, "validation_passed"
    
    def _determine_strength(
        self,
        confidence: float,
        supporting_count: int
    ) -> SignalStrength:
        """Determine signal strength for UI/alerts"""
        
        combined_score = (confidence * 0.7) + (supporting_count / 10 * 0.3)
        
        if combined_score >= 0.8:
            return SignalStrength.STRONG_BUY if confidence > 0 else SignalStrength.STRONG_SELL
        elif combined_score >= 0.6:
            return SignalStrength.BUY if confidence > 0 else SignalStrength.SELL
        else:
            return SignalStrength.NEUTRAL
    
    def _determine_market_condition(self, ind: Dict) -> MarketCondition:
        """Determine market condition using rules"""
        
        adx = ind['adx']
        gk_vol = ind['gk_volatility']
        ema_trend = ind['ema_9'] > ind['ema_50']
        
        # High volatility
        if gk_vol > 0.5:
            return MarketCondition.VOLATILE
        
        # Strong trend
        if adx > 30:
            if ema_trend:
                return MarketCondition.TRENDING_UP
            else:
                return MarketCondition.TRENDING_DOWN
        
        # Weak trend = ranging
        if adx < 20:
            return MarketCondition.RANGING
        
        return MarketCondition.UNCERTAIN
    
    def _generate_reasoning(
        self,
        action: TradeAction,
        analysis: Dict,
        ind: Dict
    ) -> str:
        """Generate human-readable reasoning"""
        
        if action == TradeAction.WAIT:
            return "No clear opportunity detected. Multiple indicators showing conflicting signals or insufficient conviction."
        
        # Get top 3 supporting indicators
        direction = 'long' if action == TradeAction.ENTER_LONG else 'short'
        
        relevant_supporting = [
            s for s in analysis['supporting']
            if s[2] == direction or s[2] == 'both'
        ][:3]
        
        reasons = []
        for ind_name, condition, _, value in relevant_supporting:
            reasons.append(f"{ind_name} {condition} ({value:.2f})" if isinstance(value, float) else f"{ind_name} {condition}")
        
        if not reasons:
            return "Signal generated by probabilistic model with weak rule confirmation."
        
        reasoning = " + ".join(reasons)
        
        # Add market condition context
        market_condition = self._determine_market_condition(ind)
        reasoning += f" | Market: {market_condition.value}"
        
        return reasoning
    
    def _calculate_confirmation_score(
        self,
        action: TradeAction,
        analysis: Dict
    ) -> float:
        """
        Calculate what % of indicators confirm the signal
        Used for dashboard display
        """
        
        if action == TradeAction.WAIT:
            return 0.0
        
        direction = 'long' if action == TradeAction.ENTER_LONG else 'short'
        
        total_checked = len(analysis['supporting']) + len(analysis['conflicting']) + len(analysis['neutral'])
        if total_checked == 0:
            return 0.0
        
        confirming = sum(
            1 for ind in analysis['supporting']
            if ind[2] == direction or ind[2] == 'both'
        )
        
        return (confirming / total_checked) * 100
    
    def _log_compliance(self, signal: Dict):
        """Log signal for hackathon compliance"""
        
        log_trade_decision(
            symbol=signal['symbol'],
            action=signal['action'],
            price=signal['current_price'],
            indicators=signal['indicators'],
            reasoning=signal['explanation']['reasoning'],
            confidence=signal['confidence'],
            position_size=None,  # Will be calculated by risk manager
            risk_reward=signal['risk_reward']
        )


# Export
__all__ = ['SignalValidatorV2']
