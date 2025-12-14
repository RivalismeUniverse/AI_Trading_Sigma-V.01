"""
AI Prompt Processor
Handles strategy generation and market analysis using AWS Bedrock
"""
import os
import json
import re
from typing import Dict, Optional
from pathlib import Path

class PromptProcessor:
    """Process trading prompts using master prompt system"""
    
    def __init__(self, bedrock_client):
        self.bedrock = bedrock_client
        self.prompts_loaded = False
        
        # Master prompts (inline for simplicity)
        self.strategy_generation_prompt = """
You are an expert quantitative trading strategy designer.

Convert the user's trading idea into a precise, executable scalping strategy.

User Request: {user_prompt}

Generate a JSON configuration with:
- strategy_name: Short descriptive name
- entry_conditions: Specific indicator thresholds (RSI, EMA, ATR, volume)
- exit_conditions: Stop loss and take profit rules
- risk_parameters: Position sizing and max risk
- timeframe: Trading timeframe (1m, 5m, 15m)
- expected_performance: Estimated win rate and profit factor

Return ONLY valid JSON, no explanation.
"""
        
        self.market_analysis_prompt = """
You are a market analysis expert.

Analyze current market conditions and provide confidence assessment.

Technical Signals:
{technical_signals}

Recent Market Data:
{market_data}

Provide analysis in JSON format:
{{
  "market_regime": "trending_bull/trending_bear/ranging/volatile",
  "confidence": 0.75,
  "signal_quality": "high/medium/low",
  "risks": ["risk1", "risk2"],
  "suggestions": ["suggestion1"],
  "reasoning": "brief explanation"
}}

Return ONLY valid JSON.
"""
        
        print("✅ Prompt processor initialized")
    
    async def generate_strategy_from_text(self, user_prompt: str) -> Dict:
        """
        Convert natural language to trading strategy
        
        Args:
            user_prompt: User's description (e.g., "RSI oversold strategy")
            
        Returns:
            Strategy configuration dictionary
        """
        try:
            print(f"🎨 Generating strategy from: '{user_prompt}'")
            
            # Format prompt
            full_prompt = self.strategy_generation_prompt.format(
                user_prompt=user_prompt
            )
            
            # Call Bedrock
            response = await self.bedrock.invoke_claude(
                prompt=full_prompt,
                max_tokens=1500,
                temperature=0.3  # Lower for structured output
            )
            
            # Parse JSON
            strategy = self._extract_json(response)
            
            if strategy:
                print(f"✅ Strategy generated: {strategy.get('strategy_name', 'Unnamed')}")
                return strategy
            else:
                print("⚠️ Failed to parse strategy, using default")
                return self._get_default_strategy()
                
        except Exception as e:
            print(f"❌ Strategy generation error: {e}")
            return self._get_default_strategy()
    
    async def analyze_market_context(
        self,
        technical_signals: Dict,
        market_data: Dict
    ) -> Dict:
        """
        AI analysis of market context
        
        Args:
            technical_signals: Python-generated technical signals
            market_data: Recent OHLCV summary
            
        Returns:
            AI analysis with confidence and suggestions
        """
        try:
            print("🧠 Running AI market analysis...")
            
            # Format prompt
            full_prompt = self.market_analysis_prompt.format(
                technical_signals=json.dumps(technical_signals, indent=2),
                market_data=json.dumps(market_data, indent=2)
            )
            
            # Call Bedrock
            response = await self.bedrock.invoke_claude(
                prompt=full_prompt,
                max_tokens=1000,
                temperature=0.5
            )
            
            # Parse JSON
            analysis = self._extract_json(response)
            
            if analysis:
                confidence = analysis.get('confidence', 0.5)
                regime = analysis.get('market_regime', 'unknown')
                print(f"✅ Analysis: {regime} (confidence: {confidence:.2f})")
                return analysis
            else:
                return self._get_default_analysis()
                
        except Exception as e:
            print(f"❌ Context analysis error: {e}")
            return self._get_default_analysis()
    
    async def chat_interaction(
        self,
        user_message: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Handle chat interface interactions
        
        Args:
            user_message: User's chat message
            context: Optional trading context (positions, performance)
            
        Returns:
            AI response text
        """
        try:
            system_prompt = """
You are an AI trading assistant for a quantitative scalping bot.

Your role:
- Explain trading concepts clearly
- Help users understand bot performance
- Answer questions about strategies
- Provide market insights
- Be concise and helpful

Always be honest about limitations and risks.
"""
            
            # Add context if available
            context_str = ""
            if context:
                context_str = f"\n\nCurrent Trading Context:\n{json.dumps(context, indent=2)}"
            
            full_prompt = f"{user_message}{context_str}"
            
            # Call Bedrock
            response = await self.bedrock.invoke_claude(
                prompt=full_prompt,
                system_prompt=system_prompt,
                max_tokens=800,
                temperature=0.7
            )
            
            return response if response else "Sorry, I encountered an error."
            
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return "Sorry, I encountered an error. Please try again."
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from AI response"""
        try:
            # Try direct parse
            return json.loads(text)
        except:
            # Try to find JSON in text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return None
    
    def _get_default_strategy(self) -> Dict:
        """Fallback default strategy"""
        return {
            "strategy_name": "Default RSI Scalping",
            "entry_conditions": {
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "ema_fast": 8,
                "ema_slow": 21,
                "volume_threshold": 1.2,
                "min_probability": 0.65
            },
            "exit_conditions": {
                "stop_loss_atr_multiplier": 1.5,
                "take_profit_atr_multiplier": 2.0,
                "max_holding_minutes": 30,
                "trailing_stop_enabled": True
            },
            "risk_parameters": {
                "max_risk_per_trade": 0.02,
                "position_sizing_method": "kelly_criterion",
                "max_concurrent_positions": 3
            },
            "timeframe": "5m",
            "expected_performance": {
                "win_rate": 0.68,
                "profit_factor": 2.1,
                "sharpe_ratio": 2.3
            }
        }
    
    def _get_default_analysis(self) -> Dict:
        """Fallback default analysis"""
        return {
            "market_regime": "normal",
            "confidence": 0.6,
            "signal_quality": "medium",
            "risks": ["AI analysis unavailable"],
            "suggestions": ["Monitor performance manually"],
            "reasoning": "Using default parameters - AI unavailable"
        }


# Test code
if __name__ == "__main__":
    import asyncio
    from bedrock_client import BedrockClient
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test():
        # Initialize Bedrock
        bedrock = BedrockClient(
            aws_access_key=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Test connection
        if not await bedrock.test_connection():
            print("❌ Bedrock connection failed")
            return
        
        # Initialize processor
        processor = PromptProcessor(bedrock)
        
        # Test 1: Generate strategy
        print("\n" + "="*50)
        print("TEST 1: Strategy Generation")
        print("="*50)
        
        strategy = await processor.generate_strategy_from_text(
            "Create an RSI oversold scalping strategy for BTC with tight stops"
        )
        print(f"\n📊 Generated Strategy:\n{json.dumps(strategy, indent=2)}")
        
        # Test 2: Market analysis
        print("\n" + "="*50)
        print("TEST 2: Market Analysis")
        print("="*50)
        
        analysis = await processor.analyze_market_context(
            technical_signals={"momentum": 0.7, "probability": 0.68},
            market_data={"current_price": 45250, "change_24h": 2.5}
        )
        print(f"\n🧠 Analysis:\n{json.dumps(analysis, indent=2)}")
        
        # Test 3: Chat
        print("\n" + "="*50)
        print("TEST 3: Chat Interaction")
        print("="*50)
        
        chat_response = await processor.chat_interaction(
            "What's the best timeframe for scalping?",
            context={"is_trading": False}
        )
        print(f"\n💬 Chat Response:\n{chat_response}")
    
    asyncio.run(test())
