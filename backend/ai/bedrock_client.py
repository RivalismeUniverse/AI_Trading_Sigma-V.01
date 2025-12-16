"""
AWS Bedrock Client - AI Integration
Claude 3.5 Sonnet for strategy generation and chat
"""

import boto3
import json
from typing import Dict, List, Optional
from datetime import datetime

from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BedrockClient:
    """AWS Bedrock client for Claude AI integration"""
    
    def __init__(self):
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = settings.BEDROCK_MODEL_ID
        
        # Load prompt templates
        self.strategy_prompt = self._load_strategy_prompt()
        self.analysis_prompt = self._load_analysis_prompt()
    
    async def chat(
        self,
        message: str,
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Chat with Claude AI
        
        Args:
            message: User message
            conversation_history: Previous conversation
            
        Returns:
            AI response
        """
        try:
            # Build messages
            messages = conversation_history or []
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Call Bedrock API
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": messages,
                    "temperature": 0.7
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            ai_message = response_body['content'][0]['text']
            
            logger.debug(f"AI response generated ({len(ai_message)} chars)")
            
            return ai_message
            
        except Exception as e:
            logger.error(f"Bedrock chat error: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    async def generate_strategy(self, prompt: str) -> Dict:
        """
        Generate trading strategy from natural language
        
        Args:
            prompt: User's strategy description
            
        Returns:
            Strategy configuration dictionary
        """
        try:
            # Build strategy generation prompt
            full_prompt = self.strategy_prompt.format(
                user_request=prompt,
                allowed_symbols=settings.ALLOWED_SYMBOLS,
                max_leverage=settings.MAX_ALLOWED_LEVERAGE,
                current_date=datetime.utcnow().strftime("%Y-%m-%d")
            )
            
            # Call Claude
            messages = [{"role": "user", "content": full_prompt}]
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 3000,
                    "messages": messages,
                    "temperature": 0.3  # Lower temperature for strategy
                })
            )
            
            response_body = json.loads(response['body'].read())
            strategy_text = response_body['content'][0]['text']
            
            # Parse strategy JSON from response
            strategy = self._parse_strategy_response(strategy_text)
            
            logger.info(f"Strategy generated: {strategy.get('name', 'Unnamed')}")
            
            return strategy
            
        except Exception as e:
            logger.error(f"Strategy generation error: {e}")
            raise
    
    async def analyze_market(
        self,
        indicators: Dict,
        symbol: str,
        timeframe: str
    ) -> str:
        """
        Get AI analysis of market conditions
        
        Args:
            indicators: Current indicator values
            symbol: Trading pair
            timeframe: Timeframe
            
        Returns:
            Market analysis text
        """
        try:
            prompt = self.analysis_prompt.format(
                symbol=symbol,
                timeframe=timeframe,
                indicators=json.dumps(indicators, indent=2)
            )
            
            messages = [{"role": "user", "content": prompt}]
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1500,
                    "messages": messages,
                    "temperature": 0.5
                })
            )
            
            response_body = json.loads(response['body'].read())
            analysis = response_body['content'][0]['text']
            
            return analysis
            
        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return "Unable to generate analysis at this time."
    
    def _parse_strategy_response(self, response_text: str) -> Dict:
        """Parse strategy JSON from AI response"""
        try:
            # Try to find JSON in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_text = response_text[start:end]
                strategy = json.loads(json_text)
                return strategy
            else:
                # Fallback: create basic strategy
                return self._create_default_strategy()
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse strategy JSON, using default")
            return self._create_default_strategy()
    
    def _create_default_strategy(self) -> Dict:
        """Create default strategy"""
        return {
            "name": "AI Generated Strategy",
            "description": "Default scalping strategy with RSI and MACD",
            "parameters": {
                "symbols": [settings.DEFAULT_SYMBOL],
                "timeframe": "5m",
                "leverage": 10,
                "risk_per_trade": 0.02,
                "indicators": {
                    "rsi_period": 14,
                    "rsi_oversold": 30,
                    "rsi_overbought": 70,
                    "macd_fast": 12,
                    "macd_slow": 26,
                    "macd_signal": 9
                },
                "entry_conditions": {
                    "long": "RSI < 30 AND MACD histogram > 0",
                    "short": "RSI > 70 AND MACD histogram < 0"
                },
                "exit_conditions": {
                    "stop_loss_atr_multiplier": 1.5,
                    "take_profit_atr_multiplier": 2.5
                }
            }
        }
    
    def _load_strategy_prompt(self) -> str:
        """Load strategy generation prompt template"""
        return """You are an expert trading strategy designer. Create a comprehensive trading strategy based on the user's request.

User Request: {user_request}

Constraints:
- Allowed symbols: {allowed_symbols}
- Maximum leverage: {max_leverage}x
- Must follow risk management best practices

Generate a complete strategy in JSON format with the following structure:
{{
    "name": "Strategy Name",
    "description": "Strategy description",
    "parameters": {{
        "symbols": ["BTC/USDT:USDT"],
        "timeframe": "5m",
        "leverage": 10,
        "risk_per_trade": 0.02,
        "indicators": {{
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70
        }},
        "entry_conditions": {{
            "long": "Conditions for long entry",
            "short": "Conditions for short entry"
        }},
        "exit_conditions": {{
            "stop_loss_atr_multiplier": 1.5,
            "take_profit_atr_multiplier": 2.5
        }}
    }}
}}

Focus on creating a practical, well-balanced strategy. Current date: {current_date}"""
    
    def _load_analysis_prompt(self) -> str:
        """Load market analysis prompt template"""
        return """Analyze the current market conditions for {symbol} on {timeframe} timeframe.

Current Indicators:
{indicators}

Provide a concise analysis covering:
1. Overall market trend (bullish/bearish/neutral)
2. Key signals from indicators
3. Potential trading opportunities
4. Risk factors to consider

Keep the analysis brief and actionable (2-3 paragraphs maximum)."""
    
    def test_connection(self) -> bool:
        """Test Bedrock connection"""
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "Test"}],
                    "temperature": 0.5
                })
            )
            return True
        except Exception as e:
            logger.error(f"Bedrock connection test failed: {e}")
            return False


# Export
__all__ = ['BedrockClient']
