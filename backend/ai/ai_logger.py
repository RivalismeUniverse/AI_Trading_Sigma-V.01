"""
AI Logger - ETHICAL VERSION using existing BedrockClient (Gemini 3 Flash)
With LOCAL BACKUP FALLBACK for reliability
"""
import re
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from ai.bedrock_client import BedrockClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AILogger:
    """
    Ethical AI Logger using REAL Gemini 3 Flash validation
    With automatic local backup if WEEX upload fails
    """
    
    def __init__(self, weex_client):
        """
        Initialize with existing clients
        Args:
            weex_client: WEEX exchange client for upload_ai_log
        """
        self.weex = weex_client
        
        # Initialize Gemini client (via your BedrockClient wrapper)
        try:
            self.gemini = BedrockClient()
            self.model_name = "Gemini 3 Flash Preview"
            logger.info("🔥 AI Logger initialized with Gemini 3 Flash")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.gemini = None
            self.model_name = "Gemini 3 Flash (unavailable)"
        
        # ✅ Setup backup directory
        self.backup_dir = 'logs/ai_backup'
        os.makedirs(self.backup_dir, exist_ok=True)

    async def validate_signal_with_real_ai(
        self,
        signal: Dict,
        indicators: Dict
    ) -> Dict:
        """
        REAL AI validation BEFORE trade execution
        Returns:
            {
                'decision': 'APPROVE' | 'REJECT',
                'confidence': float (0.0-1.0),
                'reasoning': str,
                'raw_response': str
            }
        """
        # Fallback if Gemini not available
        if not self.gemini:
            logger.warning("Gemini unavailable, using conservative default")
            return {
                'decision': 'REJECT',
                'confidence': 0.0,
                'reasoning': 'AI client unavailable - conservative rejection',
                'raw_response': ''
            }
        
        try:
            # Build validation prompt
            prompt = self._build_validation_prompt(signal, indicators)
            
            logger.info(f"🔥 Calling Gemini 3 Flash for {signal['symbol']} validation...")
            
            # Use your existing BedrockClient's chat method
            ai_response = await self.gemini.chat(
                user_message=prompt,
                conversation_history=None
            )
            
            logger.info(f"✅ Gemini response: {len(ai_response)} chars")
            
            # Parse AI response
            parsed = self._parse_ai_response(ai_response)
            
            # Log to WEEX with REAL data (with fallback)
            await self._log_to_weex(
                signal=signal,
                indicators=indicators,
                prompt=prompt,
                ai_response=parsed,
                order_id=None
            )
            
            logger.info(
                f"✅ AI Validation: {parsed['decision']} "
                f"(confidence: {parsed['confidence']:.2f})"
            )
            
            return parsed
            
        except Exception as e:
            logger.error(f"❌ AI validation failed: {e}")
            # Safe default on error
            return {
                'decision': 'REJECT',
                'confidence': 0.0,
                'reasoning': f"AI error: {str(e)}",
                'raw_response': ''
            }

    def _build_validation_prompt(self, signal: Dict, indicators: Dict) -> str:
        """Build structured prompt for Gemini"""
        action = signal['action'].value if hasattr(signal['action'], 'value') else str(signal['action'])
        
        prompt = f"""Analyze this trading signal and decide if it should be executed.

SIGNAL DETAILS:
- Symbol: {signal['symbol']}
- Action: {action}
- V1 Confidence: {signal.get('confidence', 0.0):.2f}
- V2 Confirmation: {signal.get('validation', {}).get('confirmation_score', 0.0):.1f}%

TECHNICAL INDICATORS:
- RSI: {indicators.get('rsi', 0.0):.1f}
- MACD: {indicators.get('macd_histogram', 0.0):.2f}
- Monte Carlo Probability: {indicators.get('mc_probability', 0.0):.2%}
- Z-Score: {indicators.get('z_score', 0.0):.2f}
- ADX: {indicators.get('adx', 0.0):.1f}
- Volatility: {indicators.get('gk_volatility', 0.0):.2%}

YOUR TASK:
Validate this signal. Respond in EXACT format:

DECISION: [APPROVE or REJECT]
CONFIDENCE: [0.0 to 1.0]
REASONING: [Brief 1-2 sentence explanation]

Consider:
1. Do indicators support the action?
2. Is confidence sufficient?
3. Are there conflicts?
4. Is risk acceptable?

Respond now:"""
        
        return prompt

    def _parse_ai_response(self, response: str) -> Dict:
        """Parse Gemini response into structured format"""
        try:
            # Extract DECISION
            if 'APPROVE' in response.upper() and 'REJECT' not in response.upper():
                decision = 'APPROVE'
            else:
                decision = 'REJECT'
            
            # Extract CONFIDENCE
            conf_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', response)
            confidence = float(conf_match.group(1)) if conf_match else 0.5
            confidence = max(0.0, min(1.0, confidence))
            
            # Extract REASONING
            reasoning_match = re.search(r'REASONING:\s*(.+?)(?:\n|$)', response, re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else response[:200]
            
            # Clean up reasoning
            reasoning = reasoning.replace('\n', ' ').strip()
            if len(reasoning) > 200:
                reasoning = reasoning[:197] + "..."
            
            return {
                'decision': decision,
                'confidence': confidence,
                'reasoning': reasoning,
                'raw_response': response
            }
            
        except Exception as e:
            logger.warning(f"Parse error, using safe defaults: {e}")
            return {
                'decision': 'REJECT',
                'confidence': 0.0,
                'reasoning': f"Parse error: {str(e)[:100]}",
                'raw_response': response
            }

    async def _log_to_weex(
        self,
        signal: Dict,
        indicators: Dict,
        prompt: str,
        ai_response: Dict,
        order_id: Optional[str] = None
    ):
        """
        Log ACTUAL AI decision to WEEX
        ✅ WITH AUTOMATIC LOCAL BACKUP FALLBACK
        """
        try:
            action = signal['action'].value if hasattr(signal['action'], 'value') else str(signal['action'])
            
            # Input: ACTUAL data sent to AI
            input_data = {
                "prompt": "Validate trading signal for execution decision",
                "data": {
                    "symbol": signal['symbol'],
                    "proposed_action": action,
                    "v1_confidence": float(signal.get('confidence', 0.0)),
                    "v2_confirmation": float(signal.get('validation', {}).get('confirmation_score', 0.0)),
                    "RSI": float(indicators.get('rsi', 0.0)),
                    "MACD_HISTOGRAM": float(indicators.get('macd_histogram', 0.0)),
                    "MC_PROBABILITY": float(indicators.get('mc_probability', 0.0)),
                    "Z_SCORE": float(indicators.get('z_score', 0.0)),
                    "ADX": float(indicators.get('adx', 0.0))
                }
            }
            
            # Output: ACTUAL AI response
            output_data = {
                "decision": ai_response['decision'],
                "confidence": float(ai_response['confidence']),
                "reasoning": ai_response['reasoning']
            }
            
            # Explanation: Natural language summary
            explanation = (
                f"Gemini 3 Flash analyzed {signal['symbol']} {action} signal. "
                f"Key indicators: RSI {indicators.get('rsi', 0):.1f}, "
                f"MACD {indicators.get('macd_histogram', 0):.2f}, "
                f"MC Prob {indicators.get('mc_probability', 0):.1%}. "
                f"AI validation result: {ai_response['decision']} "
                f"with {ai_response['confidence']:.0%} confidence. "
                f"Reasoning: {ai_response['reasoning']}"
            )
            
            # Trim to 1000 chars
            if len(explanation) > 1000:
                explanation = explanation[:997] + "..."
            
            # ✅ TRY Upload to WEEX (Fixed syntax here)
            result = await self.weex.upload_ai_log(
                orderId=order_id,
                stage="Signal Validation",
                model=self.model_name,
                input=input_data,
                output=output_data,
                explanation=explanation
            )
            
            if result.get('code') == '00000':
                logger.info("✅ AI Log uploaded to WEEX")
            else:
                # Upload failed, trigger fallback
                raise Exception(f"WEEX upload failed: {result}")
                
        except Exception as e:
            logger.warning(f"⚠️ WEEX AI Log upload failed: {e}")
            
            # ✅ FALLBACK: Save to local backup
            await self._save_ai_log_locally(
                signal=signal,
                indicators=indicators,
                ai_response=ai_response,
                order_id=order_id
            )

    async def _save_ai_log_locally(
        self,
        signal: Dict,
        indicators: Dict,
        ai_response: Dict,
        order_id: Optional[str]
    ):
        """
        ✅ NEW: Save AI log locally as backup when WEEX upload fails
        """
        try:
            action = signal['action'].value if hasattr(signal['action'], 'value') else str(signal['action'])
            
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "orderId": order_id,
                "stage": "Signal Validation",
                "model": self.model_name,
                "symbol": signal['symbol'],
                "action": action,
                "input": {
                    "v1_confidence": float(signal.get('confidence', 0.0)),
                    "v2_confirmation": float(signal.get('validation', {}).get('confirmation_score', 0.0)),
                    "RSI": float(indicators.get('rsi', 0.0)),
                    "MACD": float(indicators.get('macd_histogram', 0.0)),
                    "MC_PROB": float(indicators.get('mc_probability', 0.0)),
                    "Z_SCORE": float(indicators.get('z_score', 0.0)),
                    "ADX": float(indicators.get('adx', 0.0))
                },
                "output": {
                    "decision": ai_response['decision'],
                    "confidence": float(ai_response['confidence']),
                    "reasoning": ai_response['reasoning']
                },
                "weex_upload_failed": True  # Flag for manual retry later
            }
            
            # Save to JSONL file (one JSON per line)
            backup_file = os.path.join(self.backup_dir, 'ai_logs_backup.jsonl')
            with open(backup_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.info(f"💾 AI Log saved locally (backup): {backup_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save local backup: {e}")

    async def log_strategy_generation(self, strategy_config: Dict):
        """
        Optional: Log strategy generation for completeness
        ✅ WITH FALLBACK
        """
        try:
            input_data = {
                "prompt": "Design optimal trading strategy for crypto futures",
                "requirements": {
                    "market": "crypto_futures",
                    "symbols": strategy_config.get('symbols', []),
                    "max_leverage": strategy_config.get('max_leverage', 20),
                    "risk_per_trade": strategy_config.get('risk_per_trade', 0.02)
                }
            }
            
            output_data = {
                "architecture": "Hybrid dual-layer signal system",
                "components": [
                    "V1: Probabilistic category scoring",
                    "V2: Rule-based validation with 9 indicators",
                    "Gemini 3 Flash: Real-time signal validation"
                ]
            }
            
            explanation = (
                "Trading strategy combines statistical ML models with rule-based "
                "validation. Gemini 3 Flash provides real-time validation before "
                "trade execution for enhanced decision quality and compliance."
            )
            
            result = await self.weex.upload_ai_log(
                orderId=None,
                stage="Strategy Generation",
                model=self.model_name,
                input=input_data,
                output=output_data,
                explanation=explanation
            )
            
            if result.get('code') == '00000':
                logger.info("✅ Strategy generation logged to WEEX")
            else:
                raise Exception(f"Upload failed: {result}")
                
        except Exception as e:
            logger.warning(f"⚠️ Strategy log upload failed: {e}")
            
            # ✅ FALLBACK: Save locally
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "stage": "Strategy Generation",
                "model": self.model_name,
                "input": input_data,
                "output": output_data,
                "explanation": explanation,
                "weex_upload_failed": True
            }
            
            backup_file = os.path.join(self.backup_dir, 'ai_logs_backup.jsonl')
            with open(backup_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.info(f"💾 Strategy log saved locally (backup)")


__all__ = ['AILogger']
