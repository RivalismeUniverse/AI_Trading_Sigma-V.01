"""
HYBRID TRADING ENGINE - Main Orchestrator
Combines Python (90%) for speed + AI (10%) for intelligence.

This is the core autonomous trading loop that:
1. Fetches market data every 5 seconds
2. Calculates indicators (Python - fast)
3. Generates trading signals  
4. Validates with safety checker
5. Executes trades autonomously
6. AI analysis every 6 hours (strategic review)
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from backend.config import settings
from backend.exchange.weex_client import WEEXClient
from backend.exchange.safety_checker import SafetyChecker
from backend.strategies.scalping_strategy import ScalpingStrategy
from backend.strategies.technical_indicators import IndicatorCalculator
from backend.core.risk_manager import RiskManager
from backend.ai.bedrock_client import BedrockClient
from backend.ai.prompt_processor import PromptProcessor
from backend.database.db_manager import DatabaseManager
from backend.database.models import TradeStatus, TradeSide
from backend.utils.logger import setup_logger
from backend.utils.helpers import (
    calculate_position_size, calculate_pnl, generate_trade_id,
    format_timestamp
)

logger = setup_logger('hybrid_engine')

class HybridTradingEngine:
    """
    Main autonomous trading engine.
    Runs continuously in background, executing trades based on strategy.
    """
    
    def __init__(
        self,
        exchange_client: Optional[WEEXClient] = None,
        ai_client: Optional[BedrockClient] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        """Initialize hybrid engine"""
        self.exchange = exchange_client or WEEXClient(
            api_key=settings.WEEX_API_KEY,
            api_secret=settings.WEEX_API_SECRET,
            testnet=settings.WEEX_TESTNET
        )
        
        self.ai_client = ai_client or BedrockClient()
        self.prompt_processor = PromptProcessor(self.ai_client)
        self.db = db_manager or DatabaseManager(settings.DATABASE_URL)
        
        # Core components
        self.safety_checker = SafetyChecker()
        self.risk_manager = RiskManager(settings.MAX_DAILY_LOSS, settings.MAX_RISK_PER_TRADE)
        self.indicator_calculator = IndicatorCalculator()
        
        # Trading state
        self.is_running = False
        self.current_strategy: Optional[ScalpingStrategy] = None
        self.active_positions: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.symbol = settings.DEFAULT_SYMBOL
        self.timeframe = settings.DEFAULT_TIMEFRAME
        self.loop_interval = 5  # seconds
        self.ai_review_hours = settings.AI_STRATEGY_REVIEW_HOURS
        self.last_ai_review = None
        
        # Performance tracking
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.total_trades = 0
        
        logger.info("🤖 Hybrid Trading Engine initialized")
    
    async def start(self):
        """Start autonomous trading"""
        if self.is_running:
            logger.warning("Engine already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting autonomous trading engine...")
        
        # Load active strategy
        active_strategy = self.db.get_active_strategy()
        if active_strategy:
            self.load_strategy_from_db(active_strategy)
            logger.info(f"✅ Loaded active strategy: {active_strategy.name}")
        else:
            logger.warning("⚠️ No active strategy loaded. Waiting for strategy...")
        
        # Start main trading loop
        try:
            await self._main_loop()
        except Exception as e:
            logger.error(f"❌ Engine error: {e}", exc_info=True)
            self.is_running = False
    
    async def stop(self):
        """Stop trading engine"""
        logger.info("🛑 Stopping trading engine...")
        self.is_running = False
        
        # Close all open positions
        await self.close_all_positions("Engine stopped by user")
        
        logger.info("✅ Engine stopped successfully")
    
    async def _main_loop(self):
        """Main autonomous trading loop"""
        while self.is_running:
            try:
                # 1. Check if strategy is loaded
                if not self.current_strategy:
                    await asyncio.sleep(self.loop_interval)
                    continue
                
                # 2. Fetch latest market data
                ohlcv = await self.fetch_market_data()
                if ohlcv is None or len(ohlcv) < 50:
                    logger.warning("Insufficient market data")
                    await asyncio.sleep(self.loop_interval)
                    continue
                
                # 3. Calculate indicators (Python - FAST)
                indicators = self.indicator_calculator.calculate_all(ohlcv)
                
                # 4. Generate trading signals
                signal = self.current_strategy.generate_signal(ohlcv, indicators)
                
                # 5. Check if we should enter/exit trades
                await self.process_signal(signal, indicators, ohlcv)
                
                # 6. Manage open positions (check stop loss, take profit)
                await self.manage_positions(ohlcv)
                
                # 7. Periodic AI strategy review (every 6 hours)
                await self.periodic_ai_review(ohlcv, indicators)
                
                # 8. Update performance metrics
                self.update_metrics()
                
                # 9. Wait for next iteration
                await asyncio.sleep(self.loop_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(self.loop_interval)
    
    async def fetch_market_data(self) -> Optional[pd.DataFrame]:
        """Fetch latest OHLCV data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.symbol,
                self.timeframe,
                limit=200  # Get enough data for indicators
            )
            
            if ohlcv:
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return None
    
    async def process_signal(
        self, 
        signal: Dict[str, Any], 
        indicators: Dict[str, Any],
        ohlcv: pd.DataFrame
    ):
        """Process trading signal and execute if valid"""
        if signal['action'] == 'none':
            return
        
        logger.info(f"📊 Signal received: {signal['action'].upper()} "
                   f"(confidence: {signal['confidence']:.2f})")
        
        # Entry signals
        if signal['action'] in ['long', 'short']:
            await self.execute_entry(signal, indicators, ohlcv)
        
        # Exit signals
        elif signal['action'] == 'close':
            await self.execute_exit(signal['reason'])
    
    async def execute_entry(
        self,
        signal: Dict[str, Any],
        indicators: Dict[str, Any],
        ohlcv: pd.DataFrame
    ):
        """Execute entry trade"""
        try:
            # Check if we already have a position
            if self.symbol in self.active_positions:
                logger.debug("Already in position, skipping entry")
                return
            
            # Get current price
            current_price = float(ohlcv['close'].iloc[-1])
            
            # Prepare order parameters
            side = signal['action']  # 'long' or 'short'
            
            # Calculate position size
            balance = self.exchange.get_balance()
            if not balance or balance['free'] < 10:  # Minimum $10 balance
                logger.warning("Insufficient balance")
                return
            
            position_size = calculate_position_size(
                balance=balance['free'],
                risk_percent=settings.MAX_RISK_PER_TRADE,
                entry_price=current_price,
                stop_loss=signal['stop_loss'],
                leverage=self.current_strategy.leverage
            )
            
            # Risk management check
            if not self.risk_manager.can_take_trade(self.daily_pnl, balance['total']):
                logger.warning("⚠️ Risk limits exceeded, skipping trade")
                return
            
            # Safety validation (WEEX hackathon rules)
            validation = self.safety_checker.validate_order({
                'symbol': self.symbol,
                'side': side,
                'quantity': position_size,
                'leverage': self.current_strategy.leverage,
                'strategy_name': self.current_strategy.name
            })
            
            if not validation['is_valid']:
                logger.warning(f"⚠️ Safety check failed: {validation['reason']}")
                return
            
            # Execute order
            order = self.exchange.create_market_order(
                symbol=self.symbol,
                side=side,
                amount=position_size,
                leverage=self.current_strategy.leverage
            )
            
            if order:
                # Log AI decision for hackathon compliance
                self.safety_checker.log_ai_decision(
                    symbol=self.symbol,
                    action=f"ENTER_{side.upper()}",
                    decision_data={
                        'signal': signal,
                        'indicators': {k: v.value for k, v in indicators.items()},
                        'position_size': position_size,
                        'entry_price': current_price,
                        'stop_loss': signal['stop_loss'],
                        'take_profit': signal['take_profit']
                    }
                )
                
                # Create trade record
                trade_id = generate_trade_id(self.symbol)
                trade = self.db.create_trade({
                    'trade_id': trade_id,
                    'symbol': self.symbol,
                    'side': TradeSide.LONG if side == 'long' else TradeSide.SHORT,
                    'status': TradeStatus.OPEN,
                    'quantity': position_size,
                    'leverage': self.current_strategy.leverage,
                    'entry_price': current_price,
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'strategy_name': self.current_strategy.name,
                    'entry_reason': signal['reason'],
                    'ai_confidence': signal['confidence'],
                    'opened_at': datetime.utcnow(),
                    'exchange_order_id': order.get('id')
                })
                
                # Track position
                self.active_positions[self.symbol] = {
                    'trade_id': trade_id,
                    'side': side,
                    'entry_price': current_price,
                    'quantity': position_size,
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'opened_at': datetime.utcnow()
                }
                
                self.daily_trades += 1
                self.total_trades += 1
                
                logger.info(f"✅ ENTERED {side.upper()}: {position_size} @ ${current_price:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error executing entry: {e}", exc_info=True)
    
    async def execute_exit(self, reason: str = "Signal"):
        """Close all positions"""
        for symbol, position in list(self.active_positions.items()):
            try:
                # Get current price
                ohlcv = await self.fetch_market_data()
                if ohlcv is None:
                    continue
                
                current_price = float(ohlcv['close'].iloc[-1])
                
                # Close position
                close_side = 'sell' if position['side'] == 'long' else 'buy'
                order = self.exchange.create_market_order(
                    symbol=symbol,
                    side=close_side,
                    amount=position['quantity']
                )
                
                if order:
                    # Calculate P&L
                    pnl_data = calculate_pnl(
                        side=position['side'],
                        entry_price=position['entry_price'],
                        exit_price=current_price,
                        quantity=position['quantity'],
                        leverage=self.current_strategy.leverage
                    )
                    
                    # Update trade record
                    self.db.update_trade(position['trade_id'], {
                        'status': TradeStatus.CLOSED,
                        'exit_price': current_price,
                        'exit_reason': reason,
                        'pnl': pnl_data['pnl'],
                        'pnl_percent': pnl_data['pnl_percent'],
                        'closed_at': datetime.utcnow()
                    })
                    
                    # Log AI decision
                    self.safety_checker.log_ai_decision(
                        symbol=symbol,
                        action="EXIT",
                        decision_data={
                            'reason': reason,
                            'exit_price': current_price,
                            'pnl': pnl_data['pnl'],
                            'pnl_percent': pnl_data['pnl_percent']
                        }
                    )
                    
                    # Update daily P&L
                    self.daily_pnl += pnl_data['pnl']
                    
                    # Remove from active positions
                    del self.active_positions[symbol]
                    
                    logger.info(f"✅ EXITED {position['side'].upper()}: "
                              f"P&L ${pnl_data['pnl']:.2f} ({pnl_data['pnl_percent']:.2f}%)")
                
            except Exception as e:
                logger.error(f"❌ Error closing position: {e}", exc_info=True)
    
    async def manage_positions(self, ohlcv: pd.DataFrame):
        """Check stop loss and take profit for open positions"""
        current_price = float(ohlcv['close'].iloc[-1])
        
        for symbol, position in list(self.active_positions.items()):
            # Check stop loss
            if position['side'] == 'long' and current_price <= position['stop_loss']:
                logger.warning(f"🛑 Stop loss hit for {symbol}")
                await self.execute_exit("Stop loss")
            
            elif position['side'] == 'short' and current_price >= position['stop_loss']:
                logger.warning(f"🛑 Stop loss hit for {symbol}")
                await self.execute_exit("Stop loss")
            
            # Check take profit
            if position['side'] == 'long' and current_price >= position['take_profit']:
                logger.info(f"🎯 Take profit hit for {symbol}")
                await self.execute_exit("Take profit")
            
            elif position['side'] == 'short' and current_price <= position['take_profit']:
                logger.info(f"🎯 Take profit hit for {symbol}")
                await self.execute_exit("Take profit")
    
    async def periodic_ai_review(self, ohlcv: pd.DataFrame, indicators: Dict[str, Any]):
        """AI strategic review every 6 hours"""
        if not settings.AI_MODE == 'hybrid':
            return
        
        now = datetime.utcnow()
        if self.last_ai_review and (now - self.last_ai_review) < timedelta(hours=self.ai_review_hours):
            return
        
        logger.info("🧠 Running AI strategic review...")
        
        try:
            # Prepare market context
            context = {
                'symbol': self.symbol,
                'current_price': float(ohlcv['close'].iloc[-1]),
                'indicators': {k: v.value for k, v in indicators.items()},
                'active_positions': len(self.active_positions),
                'daily_pnl': self.daily_pnl,
                'daily_trades': self.daily_trades
            }
            
            # Get AI analysis
            analysis = await self.prompt_processor.analyze_market_condition(context)
            
            # Log analysis
            logger.info(f"AI Analysis: {analysis.get('summary', 'No summary')}")
            
            # If AI suggests strategy adjustment, log it
            if analysis.get('suggested_adjustments'):
                logger.info(f"AI Suggestions: {analysis['suggested_adjustments']}")
            
            self.last_ai_review = now
            
        except Exception as e:
            logger.error(f"Error in AI review: {e}")
    
    async def close_all_positions(self, reason: str = "Manual close"):
        """Close all open positions"""
        if self.active_positions:
            logger.info(f"Closing {len(self.active_positions)} positions...")
            await self.execute_exit(reason)
    
    def load_strategy_from_db(self, strategy_model):
        """Load strategy from database model"""
        self.current_strategy = ScalpingStrategy(
            name=strategy_model.name,
            symbol=strategy_model.symbol,
            timeframe=strategy_model.timeframe,
            leverage=strategy_model.leverage,
            config=strategy_model.config
        )
        
        self.symbol = strategy_model.symbol
        self.timeframe = strategy_model.timeframe
        
        logger.info(f"📋 Loaded strategy: {strategy_model.name}")
    
    def apply_strategy(self, strategy_config: Dict[str, Any]):
        """Apply new strategy configuration"""
        self.current_strategy = ScalpingStrategy(
            name=strategy_config.get('name', 'Custom Strategy'),
            symbol=strategy_config.get('symbol', self.symbol),
            timeframe=strategy_config.get('timeframe', self.timeframe),
            leverage=strategy_config.get('leverage', settings.DEFAULT_LEVERAGE),
            config=strategy_config
        )
        
        self.symbol = strategy_config.get('symbol', self.symbol)
        self.timeframe = strategy_config.get('timeframe', self.timeframe)
        
        logger.info(f"✅ Applied new strategy: {self.current_strategy.name}")
    
    def update_metrics(self):
        """Update performance metrics"""
        try:
            balance = self.exchange.get_balance()
            if not balance:
                return
            
            metrics = {
                'snapshot_time': datetime.utcnow(),
                'period': 'realtime',
                'balance': balance['total'],
                'equity': balance['total'] + self.daily_pnl,
                'total_trades': self.total_trades,
                'open_positions': len(self.active_positions),
                'daily_pnl': self.daily_pnl,
            }
            
            # Save to database every 5 minutes
            if not hasattr(self, '_last_metrics_save'):
                self._last_metrics_save = datetime.utcnow()
            
            if (datetime.utcnow() - self._last_metrics_save).total_seconds() >= 300:
                self.db.save_performance_snapshot(metrics)
                self._last_metrics_save = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            'is_running': self.is_running,
            'strategy': self.current_strategy.name if self.current_strategy else None,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'active_positions': len(self.active_positions),
            'daily_trades': self.daily_trades,
            'daily_pnl': round(self.daily_pnl, 2),
            'total_trades': self.total_trades,
            'last_ai_review': format_timestamp(self.last_ai_review) if self.last_ai_review else None
        }

# Example usage
if __name__ == "__main__":
    engine = HybridTradingEngine()
    asyncio.run(engine.start())
