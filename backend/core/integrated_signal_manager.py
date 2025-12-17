"""
Integrated Signal Manager - ORCHESTRATOR
Combines V1 (probabilistic core) + V2 (rule-based validator)
This is what the trading engine actually calls
"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime

from core.signal_generator_v1 import SignalGeneratorV1
from core.signal_validator_v2 import SignalValidatorV2
from strategies.technical_indicators import TechnicalIndicators
from utils.constants import TradeAction
from utils.logger import setup_logger

logger = setup_logger(__name__)


class IntegratedSignalManager:
    """
    Orchestrates V1 and V2 signal generation
    
    Flow:
    1. V1 generates probabilistic signal (core engine)
    2. Market regime filter (volatility, volume checks)
    3. V2 validates and explains (compliance layer)
    4. Final decision with full audit trail
    """
    
    def __init__(self, use_v2_validation: bool = True):
        self.v1_generator = SignalGeneratorV1()
        self.v2_validator = SignalValidatorV2()
        self.use_v2_validation = use_v2_validation
        
        self.signal_history = []
        self.max_history = 100
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Generate integrated trading signal
        
        Returns comprehensive signal with:
        - V1 probabilistic analysis
        - V2 rule-based validation
        - Combined decision
        - Full explanation
        """
        
        start_time = datetime.utcnow()
        
        # Step 1: V1 Core Engine (Probabilistic)
        v1_signal = self.v1_generator.generate_signal(df, symbol)
        
        # Step 2: V2 Validation (if enabled)
        if self.use_v2_validation:
            validated_signal = self.v2_validator.validate_and_explain(
                v1_signal,
                v1_signal['indicators']
            )
        else:
            # Use V1 only (for testing/comparison)
            validated_signal = v1_signal
            validated_signal['validation'] = {
                'is_valid': True,
                'validation_reason': 'v2_disabled',
                'signal_strength': 'unknown',
                'market_condition': 'unknown'
            }
        
        # Step 3: Final Decision Logic
        final_signal = self._make_final_decision(validated_signal)
        
        # Step 4: Add metadata
        final_signal['processing_time_ms'] = (datetime.utcnow() - start_time).total_seconds() * 1000
        final_signal['signal_version'] = 'integrated_v1_v2'
        
        # Store in history
        self._update_history(final_signal)
        
        # Log summary
        self._log_signal_summary(final_signal)
        
        return final_signal
    
    def _make_final_decision(self, validated_signal: Dict) -> Dict:
        """
        Make final trading decision based on V1 + V2
        
        Decision matrix:
        - V1 confident + V2 valid = Execute
        - V1 confident + V2 invalid = Review (reduce confidence)
        - V1 wait = Always respect (safety first)
        """
        
        v1_action = validated_signal['action']
        v1_confidence = validated_signal['confidence']
        
        if not self.use_v2_validation:
            # V1 only mode
            return validated_signal
        
        v2_valid = validated_signal['validation']['is_valid']
        v2_confirmation = validated_signal.get('validation', {}).get('confirmation_score', 0)
        
        # Final action and confidence
        final_action = v1_action
        final_confidence = v1_confidence
        decision_reason = ""
        
        # Decision logic
        if v1_action == TradeAction.WAIT:
            # Always respect V1 WAIT
            decision_reason = "v1_wait_respected"
        
        elif v2_valid and v2_confirmation > 50:
            # Strong agreement
            final_confidence = min(v1_confidence * 1.1, 1.0)  # Slight boost
            decision_reason = "v1_v2_strong_agreement"
        
        elif v2_valid and v2_confirmation > 30:
            # Moderate agreement
            final_confidence = v1_confidence
            decision_reason = "v1_v2_moderate_agreement"
        
        elif not v2_valid:
            # V2 validation failed
            if v1_confidence > 0.7:
                # V1 very confident, override V2
                final_confidence = v1_confidence * 0.8
                decision_reason = "v1_override_v2_high_confidence"
            else:
                # Not confident enough, downgrade to WAIT
                final_action = TradeAction.WAIT
                final_confidence = v1_confidence * 0.5
                decision_reason = f"v2_validation_failed_{validated_signal['validation']['validation_reason']}"
        
        else:
            # Low confirmation
            final_confidence = v1_confidence * 0.7
            decision_reason = "low_rule_confirmation"
        
        # Add final decision info
        validated_signal['final_decision'] = {
            'action': final_action,
            'confidence': final_confidence,
            'decision_reason': decision_reason,
            'v1_action': v1_action,
            'v1_confidence': v1_confidence,
            'v2_valid': v2_valid,
            'v2_confirmation': v2_confirmation
        }
        
        # Override top-level action/confidence
        validated_signal['action'] = final_action
        validated_signal['confidence'] = final_confidence
        
        return validated_signal
    
    def _update_history(self, signal: Dict):
        """Store signal in history for analysis"""
        self.signal_history.append({
            'timestamp': signal['timestamp'],
            'symbol': signal['symbol'],
            'action': signal['action'],
            'confidence': signal['confidence'],
            'v1_score': signal.get('adjusted_score', 0),
            'v2_valid': signal.get('validation', {}).get('is_valid', False)
        })
        
        # Keep only recent history
        if len(self.signal_history) > self.max_history:
            self.signal_history = self.signal_history[-self.max_history:]
    
    def _log_signal_summary(self, signal: Dict):
        """Log concise signal summary"""
        
        action = signal['action']
        conf = signal['confidence']
        
        if action == TradeAction.WAIT:
            logger.debug(f"Signal: WAIT | Confidence: {conf:.3f}")
        else:
            v1_score = signal.get('adjusted_score', 0)
            v2_conf = signal.get('validation', {}).get('confirmation_score', 0)
            reason = signal.get('final_decision', {}).get('decision_reason', 'unknown')
            
            logger.info(
                f"Signal: {action.value} | "
                f"Conf: {conf:.3f} | "
                f"V1: {v1_score:.3f} | "
                f"V2: {v2_conf:.0f}% | "
                f"Reason: {reason}"
            )
    
    def get_signal_statistics(self) -> Dict:
        """Get statistics from signal history"""
        
        if not self.signal_history:
            return {}
        
        total = len(self.signal_history)
        longs = sum(1 for s in self.signal_history if s['action'] == TradeAction.ENTER_LONG)
        shorts = sum(1 for s in self.signal_history if s['action'] == TradeAction.ENTER_SHORT)
        waits = sum(1 for s in self.signal_history if s['action'] == TradeAction.WAIT)
        
        avg_confidence = sum(s['confidence'] for s in self.signal_history) / total
        
        v2_valid_rate = sum(1 for s in self.signal_history if s['v2_valid']) / total * 100
        
        return {
            'total_signals': total,
            'long_signals': longs,
            'short_signals': shorts,
            'wait_signals': waits,
            'avg_confidence': avg_confidence,
            'v2_validation_rate': v2_valid_rate,
            'long_percentage': (longs / total * 100) if total > 0 else 0,
            'short_percentage': (shorts / total * 100) if total > 0 else 0,
            'wait_percentage': (waits / total * 100) if total > 0 else 0
        }
    
    def toggle_v2_validation(self, enabled: bool):
        """Enable/disable V2 validation (for testing)"""
        self.use_v2_validation = enabled
        logger.info(f"V2 validation {'enabled' if enabled else 'disabled'}")
    
    def clear_history(self):
        """Clear signal history"""
        self.signal_history = []
        logger.info("Signal history cleared")


# Export
__all__ = ['IntegratedSignalManager']
