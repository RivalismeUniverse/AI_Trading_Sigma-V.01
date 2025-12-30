"""
Hybrid Trading Engine - UPGRADED with REAL AI Validation
Now includes ETHICAL Gemini 3 Flash integration for compliance
"""

import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime
import traceback

from config import settings, get_exchange_config
from core.integrated_signal_manager import IntegratedSignalManager
from core.expectancy_engine import ExpectancyEngine
from core.regime_detector import RegimeDetector, MarketRegime
from core.enhanced_risk_manager import EnhancedRiskManager
from core.portfolio_risk_manager import PortfolioRiskManager
from core.strategy_monitor import StrategyMonitor
from core.dynamic_exit_manager import DynamicExitManager
from core.circuit_breaker import get_circuit_breaker, CircuitState
from core.api_monitor import api_monitor
from exchange.weex_client import WEEXClient
from exchange.binance_client import BinanceClient
from exchange.safety_checker import get_safety_checker
from database.db_manager import DatabaseManager
from utils.logger import setup_logger, compliance_logger
from utils.constants import TradeAction

# CRITICAL: Import REAL AI components
from ai.bedrock_client import BedrockClient
from ai.ai_logger import AILogger

logger = setup_logger(__name__)


class HybridTradingEngine:
    """
    Main autonomous trading engine - UPGRADED with ETHICAL AI
    
    New in this version:
    - REAL Gemini 3 Flash validation before trades
    - Compliant AI logging (not post-hoc fabrication)
    - AI can veto signals (adds actual value)
    """
    
    def __init__(self):
        self.is_running = False
        self.exchange_client = None
        
        # Database
        self.db_manager = DatabaseManager()
        
        # Signal generation
        self.signal_manager = IntegratedSignalManager(use_v2_validation=True)
        
        # Advanced components
        self.expectancy_engine = ExpectancyEngine(self.db_manager)
        self.regime_detector = RegimeDetector()
        self.risk_manager = EnhancedRiskManager(
            self.expectancy_engine,
            self.regime_detector,
            kelly_fraction=0.25
        )
        self.portfolio_risk = PortfolioRiskManager()
        self.strategy_monitor = StrategyMonitor()
        self.exit_manager = DynamicExitManager(
            self.regime_detector,
            self.portfolio_risk
        )
        
        # Safety
        self.safety_checker = get_safety_checker()
        self.circuit_breaker = get_circuit_breaker()
        
        # AI components (will initialize after exchange)
        self.bedrock_client = None
        self.ai_logger = None
        
        # State
        self.active_strategy = None
        self.open_positions = {}
        self.trade_count = 0
        self.total_pnl = 0.0
        
        # Performance tracking
        self.start_time = None
        self.last_balance = 0.0
        self.winning_trades = 0
        self.losing_trades = 0
        
        logger.info("✅ Hybrid Trading Engine initialized (with REAL AI pending)")
    
    async def initialize(self):
        """Initialize trading engine with REAL AI"""
        try:
            logger.info("Initializing Hybrid Trading Engine...")
            
            # Initialize exchange
            exchange_config = get_exchange_config()
            
            if exchange_config['type'] == 'weex':
                self.exchange_client = WEEXClient(
                    api_key=exchange_config['api_key'],
                    api_secret=exchange_config['api_secret'],
                    testnet=exchange_config['testnet'],
                    base_url=exchange_config.get('base_url')
                )
            elif exchange_config['type'] == 'binance':
                self.exchange_client = BinanceClient(
                    api_key=exchange_config['api_key'],
                    api_secret=exchange_config['api_secret'],
                    testnet=exchange_config['testnet']
                )
            else:
                raise ValueError(f"Unknown exchange: {exchange_config['type']}")
            
            await self.exchange_client.initialize()
            
            # CRITICAL: Initialize REAL AI components
            logger.info("🤖 Initializing Gemini 3 Flash client...")
            self.bedrock_client = BedrockClient()
            await self.badrock_client.initialize()
            
            logger.info("📝 Initializing ETHICAL AI Logger...")
            self.ai_logger = AILogger(
                weex_client=self.exchange_client,
                bedrock_client=self.bedrock_client
            )
            
            # Log strategy generation (one-time, for completeness)
            await self.ai_logger.log_strategy_generation({
                'symbols': settings.ALLOWED_SYMBOLS,
                'max_leverage': settings.DEFAULT_LEVERAGE,
                'risk_per_trade': 0.02
            })
            
            # Set leverage for allowed symbols
            for symbol in settings.ALLOWED_SYMBOLS:
                try:
                    await self.exchange_client.set_leverage(symbol, settings.DEFAULT_LEVERAGE)
                except:
                    continue
            
            # Get initial balance
            balance = await self.exchange_client.fetch_balance()
            self.last_balance = balance['total']
            
            logger.info(f"✅ Engine initialized with {exchange_config['type']}")
            logger.info(f"💰 Starting balance: ${self.last_balance:.2f}")
            logger.info("🤖 REAL AI validation ACTIVE - fully compliant mode")
            
        except Exception as e:
            logger.error(f"Failed to initialize engine: {e}")
            raise
    
    async def start(self):
        """Start autonomous trading"""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        logger.info("🚀 Starting autonomous trading with REAL AI validation...")
        
        try:
            await self.initialize()
            await self._main_loop()
        except Exception as e:
            logger.error(f"Engine error: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.is_running = False
            # Cleanup AI client
            if self.bedrock_client:
                await self.bedrock_client.close()
    
    async def stop(self):
        """Stop autonomous trading"""
        logger.info("🛑 Stopping trading engine...")
        self.is_running = False
        
        await self._close_all_positions()
        
        if self.bedrock_client:
            await self.bedrock_client.close()
        
        if self.exchange_client:
            await self.exchange_client.close()
        
        logger.info("✅ Engine stopped successfully")
    
    async def _main_loop(self):
        """Main trading loop with AI validation"""
        cycle_count = 0
        
        while self.is_running:
            try:
                cycle_start = datetime.utcnow()
                
                # Get recent trades for strategy monitoring
                recent_trades = self.db_manager.get_trades(limit=100)
                
                # Monitor strategy health
                if len(recent_trades) >= 20 and cycle_count % 5 == 0:
                    degradation = self.strategy_monitor.check_degradation(
                        recent_trades,
                        timeframe_minutes=60
                    )
                    
                    if degradation.is_degraded:
                        logger.warning(f"⚠️ Strategy degradation: {degradation.severity}")
                        
                        if degradation.severity == 'critical':
                            self.circuit_breaker.report_critical_error(
                                'STRATEGY_DEGRADATION',
                                {'report': degradation.__dict__}
                            )
                
                # Scanner logic: check all symbols
                symbols = settings.ALLOWED_SYMBOLS
                best_signal = None
                max_confidence = -1.0
                best_regime_result = None
                
                for symbol in symbols:
                    if not self.is_running:
                        break
                    
                    # Fetch OHLCV
                    df = await self.exchange_client.fetch_ohlcv(
                        symbol=symbol,
                        timeframe=settings.DEFAULT_TIMEFRAME,
                        limit=200
                    )
                    
                    if df is None or df.empty:
                        continue
                    
                    # Generate signal
                    signal = self.signal_manager.generate_signal(df, symbol)
                    
                    if signal['action'] == TradeAction.WAIT:
                        continue
                    
                    # Detect regime
                    regime_result = self.regime_detector.detect(df, signal['indicators'])
                    
                    # Check if should trade in this regime
                    should_trade, reason = self.regime_detector.should_trade(regime_result)
                    
                    if not should_trade:
                        logger.debug(f"Skipping {symbol}: {reason}")
                        continue
                    
                    # Track best signal
                    if signal['confidence'] > max_confidence:
                        max_confidence = signal['confidence']
                        best_signal = signal
                        best_regime_result = regime_result
                        logger.info(
                            f"📊 {symbol}: {signal['action'].value} "
                            f"(Conf: {signal['confidence']:.3f}, "
                            f"Regime: {regime_result['regime'].value})"
                        )
                
                # Execute best signal if confidence threshold met
                if best_signal and max_confidence >= settings.MIN_CONFIDENCE:
                    logger.info(f"🎯 SCANNER PICK: {best_signal['symbol']} (score: {max_confidence:.3f})")
                    await self._process_signal(best_signal, best_regime_result)
                
                # Manage existing positions
                await self._manage_positions_advanced()
                
                # Update metrics
                await self._update_metrics()
                
                cycle_time = (datetime.utcnow() - cycle_start).total_seconds()
                cycle_count += 1
                
                if cycle_count % 10 == 0:
                    logger.info(f"📈 Cycle #{cycle_count} completed in {cycle_time*1000:.0f}ms")
                
                await asyncio.sleep(settings.TRADE_CYCLE_SECONDS)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
    
    async def _process_signal(self, signal: Dict, regime_result: Dict):
        """
        Process signal with REAL AI validation
        
        KEY CHANGE: AI validation BEFORE execution (ethical & compliant)
        """
        symbol = signal['symbol']
        action = signal['action']
        
        # Check circuit breaker
        allowed, reason = self.circuit_breaker.check_execution_allowed(action)
        if not allowed:
            logger.warning(f"Circuit breaker blocked: {reason}")
            return
        
        # Only open new positions
        if action not in [TradeAction.ENTER_LONG, TradeAction.ENTER_SHORT]:
            return
        
        # Check if already have position
        if symbol in self.open_positions:
            logger.debug(f"Already have position in {symbol}")
            return
        
        # Check max positions
        if len(self.open_positions) >= settings.MAX_OPEN_POSITIONS:
            logger.debug("Max open positions reached")
            return
        
        # CRITICAL: REAL AI VALIDATION BEFORE PROCEEDING
        logger.info(f"🤖 Requesting Gemini 3 Flash validation for {symbol}...")
        
        ai_validation = await self.ai_logger.validate_signal_with_real_ai(
            signal=signal,
            indicators=signal['indicators']
        )
        
        # AI VETO CHECK - This is REAL decision-making
        if ai_validation['decision'] == 'REJECT':
            logger.warning(
                f"❌ AI REJECTED signal for {symbol}: "
                f"{ai_validation['reasoning']}"
            )
            return
        
        # AI confidence check
        if ai_validation['confidence'] < 0.4:
            logger.warning(
                f"⚠️ AI confidence too low ({ai_validation['confidence']:.2f}) "
                f"for {symbol}, skipping"
            )
            return
        
        logger.info(
            f"✅ AI APPROVED {symbol} with {ai_validation['confidence']:.0%} confidence"
        )
        
        # Merge AI validation into signal
        signal['ai_validated'] = True
        signal['ai_confidence'] = ai_validation['confidence']
        signal['ai_reasoning'] = ai_validation['reasoning']
        
        # Get balance
        balance_data = await self.exchange_client.fetch_balance()
        current_balance = balance_data['total']
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            balance=current_balance,
            entry_price=signal['current_price'],
            stop_loss_price=signal['stop_loss'],
            leverage=settings.DEFAULT_LEVERAGE,
            symbol=symbol,
            regime_result=regime_result,
            confidence=signal['confidence']
        )
        
        if position_size == 0:
            logger.info(f"Position size = 0 for {symbol}, skipping")
            return
        
        # Portfolio risk validation
        is_valid_portfolio, portfolio_error = self.portfolio_risk.validate_new_position(
            new_symbol=symbol,
            new_size=position_size,
            new_entry_price=signal['current_price'],
            open_positions=list(self.open_positions.values()),
            balance=current_balance
        )
        
        if not is_valid_portfolio:
            logger.warning(f"Portfolio risk check failed: {portfolio_error}")
            return
        
        # Risk validation
        is_valid_risk, risk_error = self.risk_manager.validate_risk(
            position_size=position_size,
            entry_price=signal['current_price'],
            balance=current_balance,
            open_positions=len(self.open_positions),
            leverage=settings.DEFAULT_LEVERAGE
        )
        
        if not is_valid_risk:
            logger.warning(f"Risk validation failed: {risk_error}")
            return
        
        # Safety checker
        is_valid_safety, safety_error = self.safety_checker.validate_trade(
            symbol=symbol,
            side='buy' if action == TradeAction.ENTER_LONG else 'sell',
            amount=position_size,
            leverage=settings.DEFAULT_LEVERAGE,
            price=signal['current_price'],
            account_balance=current_balance
        )
        
        if not is_valid_safety:
            logger.warning(f"Safety check failed: {safety_error}")
            return
        
        # All checks passed (including AI) - execute trade
        await self._execute_trade(signal, position_size, regime_result)
    
    async def _execute_trade(self, signal: Dict, position_size: float, regime_result: Dict):
        """Execute market order (AI already validated)"""
        try:
            symbol = signal['symbol']
            action = signal['action']
            side = 'buy' if action == TradeAction.ENTER_LONG else 'sell'
            
            # Create market order
            order = await self.exchange_client.create_market_order(
                symbol=symbol,
                side=side,
                amount=position_size,
                params={'leverage': settings.DEFAULT_LEVERAGE}
            )
            
            # Note: AI Log already sent in validate_signal_with_real_ai()
            # No post-hoc logging needed - we're fully compliant!
            
            # Create stop loss
            stop_side = 'sell' if action == TradeAction.ENTER_LONG else 'buy'
            stop_order = await self.exchange_client.create_stop_loss_order(
                symbol=symbol,
                side=stop_side,
                amount=position_size,
                stop_price=signal['stop_loss'],
                params={'reduceOnly': True}
            )
            
            # Store position
            self.open_positions[symbol] = {
                'entry_order': order,
                'stop_order': stop_order,
                'signal': signal,
                'entry_time': datetime.utcnow(),
                'entry_price': signal['current_price'],
                'position_size': position_size,
                'side': action,
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'entry_regime': regime_result['regime'],
                'ai_validated': signal.get('ai_validated', False),
                'ai_confidence': signal.get('ai_confidence', 0.0),
                'highest_price': signal['current_price'],
                'lowest_price': signal['current_price']
            }
            
            self.trade_count += 1
            
            # Save to database
            self.db_manager.save_trade({
                'symbol': symbol,
                'action': action.value,
                'entry_price': signal['current_price'],
                'position_size': position_size,
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'leverage': settings.DEFAULT_LEVERAGE,
                'confidence': signal['confidence'],
                'ai_confidence': signal.get('ai_confidence', 0.0),
                'entry_time': datetime.utcnow(),
                'indicators': signal['indicators']
            })
            
            logger.info(
                f"✅ Trade #{self.trade_count} opened: {symbol} {action.value} "
                f"Size: {position_size:.6f} @ ${signal['current_price']:.2f} "
                f"(AI: {signal.get('ai_confidence', 0):.0%}, "
                f"Regime: {regime_result['regime'].value})"
            )
            
        except Exception as e:
            logger.error(f"Execution failed for {symbol}: {e}")
            self.circuit_breaker.report_order_failure({'error': str(e), 'symbol': symbol})
    
    async def _manage_positions_advanced(self):
        """Advanced position management"""
        for symbol, position in list(self.open_positions.items()):
            try:
                # Fetch current price
                ticker = await self.exchange_client.fetch_ticker(symbol)
                current_price = ticker['last']
                
                # Update highest/lowest
                if current_price > position['highest_price']:
                    position['highest_price'] = current_price
                if current_price < position['lowest_price']:
                    position['lowest_price'] = current_price
                
                # Fetch current OHLCV
                df = await self.exchange_client.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=settings.DEFAULT_TIMEFRAME,
                    limit=200
                )
                
                if df is None or df.empty:
                    continue
                
                # Calculate indicators
                signal = self.signal_manager.generate_signal(df, symbol)
                indicators = signal['indicators']
                
                # Detect current regime
                regime_result = self.regime_detector.detect(df, indicators)
                current_regime = regime_result['regime']
                
                # Get balance
                balance_data = await self.exchange_client.fetch_balance()
                balance = balance_data['total']
                
                # Check dynamic exit conditions
                should_exit, exit_reason, exit_details = self.exit_manager.should_exit(
                    position=position,
                    current_price=current_price,
                    current_regime=current_regime,
                    indicators=indicators,
                    open_positions=list(self.open_positions.values()),
                    balance=balance
                )
                
                if should_exit:
                    await self._close_position(
                        symbol,
                        f"{exit_reason.value}_{exit_details if exit_details else ''}"
                    )
                    continue
                
                # Check if position still exists on exchange
                exchange_positions = await self.exchange_client.fetch_positions(symbol)
                if not exchange_positions or all(float(p.get('contracts', 0)) == 0 for p in exchange_positions):
                    await self._close_position_record(symbol, position, "stop_loss_exchange")
                
            except Exception as e:
                logger.error(f"Position management error ({symbol}): {e}")
    
    async def _close_position(self, symbol: str, reason: str):
        """Close position manually"""
        try:
            await self.exchange_client.close_position(symbol)
            
            if symbol in self.open_positions:
                await self._close_position_record(symbol, self.open_positions[symbol], reason)
                
        except Exception as e:
            logger.error(f"Close error for {symbol}: {e}")
    
    async def _close_position_record(self, symbol: str, position: Dict, reason: str):
        """Record position closure"""
        if symbol not in self.open_positions:
            return
        
        try:
            # Fetch final price
            ticker = await self.exchange_client.fetch_ticker(symbol)
            exit_price = ticker['last']
            
            # Calculate P&L
            entry_price = position['entry_price']
            size = position['position_size']
            side = position['side']
            
            if side == TradeAction.ENTER_LONG:
                pnl = (exit_price - entry_price) * size
            else:
                pnl = (entry_price - exit_price) * size
            
            self.total_pnl += pnl
            
            if pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            logger.info(
                f"🔒 Position closed: {symbol} | "
                f"P&L: ${pnl:.2f} | Reason: {reason}"
            )
            
            # Remove from open positions
            del self.open_positions[symbol]
            
        except Exception as e:
            logger.error(f"Error recording position closure for {symbol}: {e}")
    
    async def _close_all_positions(self):
        """Close all open positions"""
        for symbol in list(self.open_positions.keys()):
            await self._close_position(symbol, "engine_shutdown")
    
    async def _update_metrics(self):
        """Update performance metrics"""
        if not self.exchange_client:
            return
        
        try:
            balance = await self.exchange_client.fetch_balance()
            current_balance = balance['total']
            
            # Record for safety checker
            self.safety_checker.record_trade({
                'pnl': current_balance - self.last_balance
            })
            
        except Exception as e:
            logger.debug(f"Metrics update error: {e}")
    
    async def get_status(self) -> Dict:
        """Get engine status"""
        balance_val = 0
        if self.exchange_client:
            try:
                b = await self.exchange_client.fetch_balance()
                balance_val = b['total']
            except:
                pass
        
        # Get expectancy summary
        expectancy_summary = self.expectancy_engine.get_performance_summary()
        
        # Get portfolio exposure
        portfolio_exposure = {}
        if self.open_positions:
            portfolio_exposure = self.portfolio_risk.get_portfolio_exposure_breakdown(
                list(self.open_positions.values()),
                balance_val
            )
        
        return {
            'is_running': self.is_running,
            'exchange': settings.EXCHANGE,
            'balance': balance_val,
            'open_positions': len(self.open_positions),
            'total_trades': self.trade_count,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_pnl': self.total_pnl,
            'uptime': (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
            'expectancy_metrics': expectancy_summary,
            'portfolio_exposure': portfolio_exposure,
            'ai_validation_active': self.bedrock_client is not None
        }
    
    async def get_balance(self) -> Dict:
        """Get account balance"""
        if not self.exchange_client:
            return {'total': 0, 'free': 0}
        return await self.exchange_client.fetch_balance()
    
    async def get_open_positions(self) -> List[Dict]:
        """Get open positions"""
        return list(self.open_positions.values())


__all__ = ['HybridTradingEngine']
