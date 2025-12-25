"""
Google Gemini 3 Client - AI Trading SIGMA Integration
Optimized for Gemini 3 Flash Preview (Experimental)
"""

import os
import json
import logging
from typing import Dict, List, Optional
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Memastikan variabel di .env terbaca sebelum client diinisialisasi
load_dotenv()

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Google Gemini client with same interface as BedrockClient.
    Provides advanced trading strategy generation and market analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client with Gemini 3 Flash"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Get one at: https://aistudio.google.com/app/apikey"
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Menggunakan Gemini 3 Flash Preview sesuai ketersediaan di akun kamu
        self.model = genai.GenerativeModel(
            model_name='gemini-3-flash-preview',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 8192,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        )
        
        self.system_prompt = self._load_system_prompt()
        logger.info("✓ Gemini 3 Flash Client initialized successfully")
    
    def _load_system_prompt(self) -> str:
        """Load system prompt for trading assistant"""
        return """You are an expert cryptocurrency trading assistant for AI Trading SIGMA.

Your role:
- Analyze market conditions and technical indicators
- Generate trading strategies based on user requirements
- Explain trading signals in clear, actionable language
- Provide risk management recommendations

Key constraints:
- Only use allowed symbols: BTC, ETH, SOL, ADA, XRP, LTC, DOGE, BNB (all vs USDT)
- Maximum leverage: 20x
- Always include risk management in strategies
- Response format: Professional, data-driven, actionable."""

    async def chat(
        self, 
        user_message: str, 
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """Chat with Gemini 3"""
        try:
            messages = []
            if conversation_history:
                for msg in conversation_history:
                    role = 'user' if msg.get('role') == 'user' else 'model'
                    content = msg.get('content', '')
                    messages.append({'role': role, 'parts': [content]})
            
            # Start chat with history
            chat_session = self.model.start_chat(history=messages)
            
            # Send current message with system context
            full_prompt = f"{self.system_prompt}\n\nUser: {user_message}"
            response = chat_session.send_message(full_prompt)
            
            result = response.text.strip()
            logger.info(f"Gemini 3 Chat: {len(user_message)} chars in, {len(result)} chars out")
            return result
            
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            return f"I encountered an error: {str(e)}. Please try again."

    async def generate_strategy(self, prompt: str) -> Dict:
        """Generate trading strategy in valid JSON format"""
        try:
            strategy_prompt = f"""{self.system_prompt}
User wants to create a trading strategy: "{prompt}"

Generate a complete trading strategy in JSON format with these fields:
{{
    "name": "Strategy name",
    "description": "Brief description",
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
            "long": "Condition for long",
            "short": "Condition for short"
        }},
        "exit_conditions": {{
            "stop_loss_atr_multiplier": 1.5,
            "take_profit_atr_multiplier": 2.5
        }}
    }}
}}
Return ONLY valid JSON."""

            response = self.model.generate_content(strategy_prompt)
            result = response.text.strip()
            
            # Clean JSON from markdown blocks
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0].strip()
            elif '```' in result:
                result = result.split('```')[1].split('```')[0].strip()
            
            strategy = json.loads(result)
            logger.info(f"✓ Strategy '{strategy.get('name')}' generated by Gemini 3")
            return strategy
            
        except Exception as e:
            logger.error(f"Strategy generation error: {e}")
            return self._get_default_strategy(prompt)

    def _get_default_strategy(self, prompt: str) -> Dict:
        """Fallback strategy if generation fails"""
        return {
            "name": "Default RSI Strategy",
            "description": f"Fallback strategy for: {prompt[:50]}",
            "parameters": {
                "symbols": ["BTC/USDT:USDT"],
                "timeframe": "5m",
                "leverage": 10,
                "indicators": {"rsi_period": 14, "rsi_oversold": 30}
            }
        }

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self.model.generate_content("OK")
            return len(response.text) > 0
        except:
            return False

# Export as BedrockClient to maintain compatibility with main.py
BedrockClient = GeminiClient

__all__ = ['GeminiClient', 'BedrockClient']

