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
    """
    
    def __init__(self, use_v2_validation: bool = True):
        self.v1_generator = SignalGeneratorV1()
        self.v2_validator = SignalValidatorV2()
        self.use_v2_validation = use_v2_validation
        
        self.signal_history = []
        self.max_history = 100
    
    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Generate integrated trading signal with safety guards
        """
        start_time = datetime.utcnow()
        
        # Step 1: V1 Core Engine (Probabilistic)
        v1_signal = self.v1_generator.generate_signal(df, symbol)
        
        # --- SAFETY GUARD: Cek apakah v1_signal valid ---
        if not v1_signal or 'indicators' not in v1_signal:
            logger.warning(f"V1 signal incomplete for {symbol}, generating neutral WAIT signal.")
            v1_signal = {
                'action': TradeAction.WAIT,
                'confidence': 0,
                'indicators': {},
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol
            }

        # Step 2: V2 Validation (if enabled)
        if self.use_v2_validation and v1_signal['action'] != TradeAction.WAIT:
            try:
                validated_signal = self.v2_validator.validate_and_explain(
                    v1_signal,
                    v1_signal['indicators']
                )
            except Exception as e:
                logger.error(f"V2 Validation Error: {e}")
                validated_signal = v1_signal # Fallback ke V1 saja kalau V2 crash
        else:
            # Use V1 only (for testing/comparison or when action is WAIT)
            validated_signal = v1_signal
            if 'validation' not in validated_signal:
                validated_signal['validation'] = {
                    'is_valid': True,
                    'validation_reason': 'v2_disabled_or_wait',
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
        """
        v1_action = validated_signal.get('action', TradeAction.WAIT)
        v1_confidence = validated_signal.get('confidence', 0)
        
        if not self.use_v2_validation or v1_action == TradeAction.WAIT:
            return validated_signal
        
        # Ambil data validation dengan default value aman
        v2_data = validated_signal.get('validation', {})
        v2_valid = v2_data.get('is_valid', False)
        v2_confirmation = v2_data.get('confirmation_score', 0)
        
        final_action = v1_action
        final_confidence = v1_confidence
        decision_reason = ""
        
        # Decision logic
        if v2_valid and v2_confirmation > 50:
            final_confidence = min(v1_confidence * 1.1, 1.0)
            decision_reason = "v1_v2_strong_agreement"
        elif v2_valid and v2_confirmation > 30:
            decision_reason = "v1_v2_moderate_agreement"
        elif not v2_valid:
            if v1_confidence > 0.7:
                final_confidence = v1_confidence * 0.8
                decision_reason = "v1_override_v2_high_confidence"
            else:
                final_action = TradeAction.WAIT
                final_confidence = v1_confidence * 0.5
                decision_reason = f"v2_validation_failed_{v2_data.get('validation_reason', 'unknown')}"
        else:
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
        
        validated_signal['action'] = final_action
        validated_signal['confidence'] = final_confidence
        
        return validated_signal
    
    def _update_history(self, signal: Dict):
        self.signal_history.append({
            'timestamp': signal.get('timestamp'),
            'symbol': signal.get('symbol'),
            'action': signal.get('action'),
            'confidence': signal.get('confidence'),
            'v1_score': signal.get('adjusted_score', 0),
            'v2_valid': signal.get('validation', {}).get('is_valid', False)
        })
        if len(self.signal_history) > self.max_history:
            self.signal_history = self.signal_history[-self.max_history:]
    
    def _log_signal_summary(self, signal: Dict):
        action = signal.get('action', TradeAction.WAIT)
        conf = signal.get('confidence', 0)
        
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
        if not self.signal_history: return {}
        total = len(self.signal_history)
        longs = sum(1 for s in self.signal_history if s['action'] == TradeAction.ENTER_LONG)
        shorts = sum(1 for s in self.signal_history if s['action'] == TradeAction.ENTER_SHORT)
        avg_conf = sum(s['confidence'] for s in self.signal_history) / total
        return {
            'total_signals': total,
            'long_signals': longs,
            'short_signals': shorts,
            'avg_confidence': avg_conf
        }

    def toggle_v2_validation(self, enabled: bool):
        self.use_v2_validation = enabled
        logger.info(f"V2 validation {'enabled' if enabled else 'disabled'}")

    def clear_history(self):
        self.signal_history = []

__all__ = ['IntegratedSignalManager']