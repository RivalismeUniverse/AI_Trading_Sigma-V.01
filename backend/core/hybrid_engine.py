"""
Hybrid Trading Engine - The Core of AI Trading SIGMA
Autonomous trading loop with 100ms execution cycle
90% Python (Speed) + 10% AI (Intelligence)
"""

import asyncio
import time
from typing import Dict, List, Optional
from datetime import datetime
import traceback

from config import settings, get_exchange_config
from core.integrated_signal_manager import IntegratedSignalManager
from core.risk_manager import RiskManager
from core.circuit_breaker import get_circuit_breaker, CircuitState
from core.api_monitor import api_monitor
from exchange.weex_client import WEEXClient
from exchange.binance_client import BinanceClient
from exchange.safety_checker import get_safety_checker
from database.db_manager import DatabaseManager
from utils.logger import setup_logger, compliance_logger
from utils.constants import TradeAction

logger = setup_logger(__name__)


class HybridTradingEngine:
    """
    Main autonomous trading engine
    Runs continuous loop for signal generation and trade execution
    """
    
    def __init__(self):
        self.is_running = False
        self.exchange_client = None
        self.signal_manager = IntegratedSignalManager(use_v2_validation=True)
        self.risk_manager = RiskManager()
        self.safety_checker = get_safety_checker()
        self.circuit_breaker = get_circuit_breaker()
        self.db_manager = DatabaseManager()
        
        self.active_strategy = None
        self.open_positions = {}
        self.trade_count = 0
        self.total_pnl = 0.0
        
        # Performance tracking
        self.start_time = None
        self.last_balance = 0.0
        self.winning_trades = 0
        self.losing_trades = 0
    
    async def initialize(self):
        """Initialize trading engine"""
        try:
            logger.info("Initializing Hybrid Trading Engine...")
            
            # Initialize exchange client based on config
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
            
            # Set leverage
            await self.exchange_client.set_leverage(
                settings.DEFAULT_SYMBOL,
                settings.DEFAULT_LEVERAGE
            )
            
            # Get initial balance
            balance = await self.exchange_client.fetch_balance()
            self.last_balance = balance['total']
            
            logger.info(f"✅ Engine initialized with {exchange_config['type']}")
            logger.info(f"💰 Starting balance: ${self.last_balance:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to initialize engine: {e}")
            raise
    
    async def start(self):
        """Start autonomous trading"""
        if self.is_running:
            logger.warning("Engine is already running")
            return
        
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        logger.info("🚀 Starting autonomous trading...")
        
        try:
            await self.initialize()
            await self._main_loop()
        except Exception as e:
            logger.error(f"Engine error: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.is_running = False
    
    async def stop(self):
        """Stop autonomous trading"""
        logger.info("🛑 Stopping trading engine...")
        self.is_running = False
        
        # Close all positions
        await self._close_all_positions()
        
        # Close exchange connection
        if self.exchange_client:
            await self.exchange_client.close()
        
        # Generate final report
        await self._generate_final_report()
        
        logger.info("✅ Engine stopped successfully")
    
    async def _main_loop(self):
        """
        Main trading loop
        Executes every TRADE_CYCLE_SECONDS (default 5 seconds)
        """
        cycle_count = 0
        
        while self.is_running:
            try:
                cycle_start = datetime.utcnow()
                
                # 1. Fetch market data
                df = await self.exchange_client.fetch_ohlcv(
                    symbol=settings.DEFAULT_SYMBOL,
                    timeframe=settings.DEFAULT_TIMEFRAME,
                    limit=200
                )
                
                # 2. Generate trading signal (Integrated V1+V2)
                signal = self.signal_manager.generate_signal(
                    df,
                    settings.DEFAULT_SYMBOL
                )
                
                # 3. Process signal
                await self._process_signal(signal)
                
                # 4. Manage open positions
                await self._manage_positions()
                
                # 5. Update performance metrics
                await self._update_metrics()
                
                # Calculate cycle time
                cycle_time = (datetime.utcnow() - cycle_start).total_seconds()
                cycle_count += 1
                
                if cycle_count % 12 == 0:  # Log every minute
                    logger.info(f"✅ Cycle #{cycle_count} completed in {cycle_time*1000:.0f}ms")
                
                # Wait for next cycle
                await asyncio.sleep(settings.TRADE_CYCLE_SECONDS)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _process_signal(self, signal: Dict):
        """Process trading signal and execute if valid"""
        
        action = signal['action']
        
        if action == TradeAction.WAIT:
            return
        
        # Check circuit breaker FIRST
        allowed, reason = self.circuit_breaker.check_execution_allowed(action)
        if not allowed:
            logger.warning(f"Trade blocked by circuit breaker: {reason}")
            return
        
        # In THROTTLE mode, skip low confidence signals
        if self.circuit_breaker.state == CircuitState.THROTTLE:
            if signal['confidence'] < 0.7:
                logger.info(f"Skipping low confidence signal in THROTTLE mode: {signal['confidence']:.2f}")
                return
        
        # Check if we should enter a trade
        if action in [TradeAction.ENTER_LONG, TradeAction.ENTER_SHORT]:
            
            # Check if we already have a position
            if settings.DEFAULT_SYMBOL in self.open_positions:
                logger.debug("Already have open position, skipping")
                return
            
            # Get current balance
            balance = await self.exchange_client.fetch_balance()
            current_balance = balance['total']
            
            # Calculate position size
            position_size = self.risk_manager.calculate_position_size(
                balance=current_balance,
                risk_pct=settings.MAX_RISK_PER_TRADE,
                entry_price=signal['current_price'],
                stop_loss_price=signal['stop_loss'],
                leverage=settings.DEFAULT_LEVERAGE
            )
            
            # Validate with safety checker
            is_valid, error = self.safety_checker.validate_trade(
                symbol=settings.DEFAULT_SYMBOL,
                side='buy' if action == TradeAction.ENTER_LONG else 'sell',
                amount=position_size,
                leverage=settings.DEFAULT_LEVERAGE,
                price=signal['current_price'],
                account_balance=current_balance
            )
            
            if not is_valid:
                logger.warning(f"Trade validation failed: {error}")
                compliance_logger.log_execution_failure({
                    "symbol": settings.DEFAULT_SYMBOL,
                    "reason": error,
                    "signal": signal
                })
                return
            
            # Execute trade
            await self._execute_trade(signal, position_size)
    
    async def _execute_trade(self, signal: Dict, position_size: float):
        """Execute trade based on signal"""
        try:
            action = signal['action']
            side = 'buy' if action == TradeAction.ENTER_LONG else 'sell'
            
            # Track execution start time
            start_time = time.time()
            
            # Create market order
            order = await self.exchange_client.create_market_order(
                symbol=settings.DEFAULT_SYMBOL,
                side=side,
                amount=position_size,
                params={'leverage': settings.DEFAULT_LEVERAGE}
            )
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            api_monitor._record_call('create_market_order', execution_time_ms, None)
            
            # Check slippage
            expected_price = signal['current_price']
            actual_price = order.get('price', expected_price)
            if actual_price != expected_price:
                self.circuit_breaker.report_slippage(expected_price, actual_price)
            
            logger.info(f"✅ Order executed: {side} {position_size} @ {signal['current_price']}")
            
            # Create stop loss
            stop_side = 'sell' if action == TradeAction.ENTER_LONG else 'buy'
            stop_order = await self.exchange_client.create_stop_loss_order(
                symbol=settings.DEFAULT_SYMBOL,
                side=stop_side,
                amount=position_size,
                stop_price=signal['stop_loss'],
                params={'reduceOnly': True}
            )
            
            # Store position
            self.open_positions[settings.DEFAULT_SYMBOL] = {
                'entry_order': order,
                'stop_order': stop_order,
                'signal': signal,
                'entry_time': datetime.utcnow(),
                'entry_price': signal['current_price'],
                'position_size': position_size,
                'side': action
            }
            
            self.trade_count += 1
            
            # Log to database
            self.db_manager.save_trade({
                'symbol': settings.DEFAULT_SYMBOL,
                'action': action,
                'entry_price': signal['current_price'],
                'position_size': position_size,
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'confidence': signal['confidence'],
                'timestamp': datetime.utcnow()
            })
            
            logger.info(f"📊 Trade #{self.trade_count} opened")
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            
            # Report failure to circuit breaker
            self.circuit_breaker.report_order_failure({
                'symbol': settings.DEFAULT_SYMBOL,
                'error': str(e),
                'signal': signal
            })
            
            compliance_logger.log_execution_failure({
                "symbol": settings.DEFAULT_SYMBOL,
                "error": str(e),
                "signal": signal
            })
    
    async def _manage_positions(self):
        """Manage open positions (check SL/TP, trailing stop, etc.)"""
        
        for symbol, position in list(self.open_positions.items()):
            try:
                # Fetch current positions from exchange
                exchange_positions = await self.exchange_client.fetch_positions(symbol)
                
                # If position is closed
                if not exchange_positions:
                    await self._close_position_record(symbol, position)
                else:
                    # Check if take profit reached
                    current_price = (await self.exchange_client.fetch_ticker(symbol))['last']
                    
                    signal = position['signal']
                    if position['side'] == TradeAction.ENTER_LONG:
                        if current_price >= signal['take_profit']:
                            await self._close_position(symbol, "take_profit")
                    elif position['side'] == TradeAction.ENTER_SHORT:
                        if current_price <= signal['take_profit']:
                            await self._close_position(symbol, "take_profit")
                            
            except Exception as e:
                logger.error(f"Error managing position {symbol}: {e}")
    
    async def _close_position(self, symbol: str, reason: str):
        """Close position manually"""
        try:
            result = await self.exchange_client.close_position(symbol)
            await self._close_position_record(symbol, self.open_positions[symbol], reason)
            logger.info(f"✅ Position closed: {symbol} - {reason}")
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
    
    async def _close_position_record(self, symbol: str, position: Dict, reason: str = "stop_loss"):
        """Update position record after closure"""
        
        # Fetch final trades to calculate P&L
        trades = await self.exchange_client.fetch_my_trades(symbol, limit=10)
        
        # Calculate P&L (simplified)
        pnl = 0.0
        if trades:
            entry_value = position['entry_price'] * position['position_size']
            exit_price = trades[-1]['price']
            exit_value = exit_price * position['position_size']
            
            if position['side'] == TradeAction.ENTER_LONG:
                pnl = exit_value - entry_value
            else:
                pnl = entry_value - exit_value
        
        # Update stats
        self.total_pnl += pnl
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Log P&L
        compliance_logger.log_pnl({
            "symbol": symbol,
            "pnl": pnl,
            "reason": reason,
            "entry_price": position['entry_price'],
            "position_size": position['position_size']
        })
        
        # Remove from open positions
        del self.open_positions[symbol]
        
        logger.info(f"💰 P&L: ${pnl:.2f} ({reason})")
    
    async def _close_all_positions(self):
        """Close all open positions"""
        for symbol in list(self.open_positions.keys()):
            await self._close_position(symbol, "manual_close")
    
    async def _update_metrics(self):
        """Update performance metrics"""
        try:
            balance = await self.exchange_client.fetch_balance()
            current_balance = balance['total']
            
            # Calculate daily P&L
            daily_pnl = current_balance - self.last_balance
            
            # Update safety checker
            self.safety_checker.record_trade({
                'pnl': daily_pnl
            })
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    async def _generate_final_report(self):
        """Generate final performance report"""
        
        total_trades = self.winning_trades + self.losing_trades
        win_rate = (self.winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        report = f"""
{'='*80}
AI TRADING SIGMA - FINAL REPORT
{'='*80}
Total Trades:        {total_trades}
Winning Trades:      {self.winning_trades}
Losing Trades:       {self.losing_trades}
Win Rate:            {win_rate:.1f}%
Total P&L:           ${self.total_pnl:.2f}
{'='*80}
"""
        
        logger.info(report)
        compliance_logger.update_summary(report)
    
    async def apply_strategy(self, strategy: Dict):
        """Apply new trading strategy"""
        # Validate strategy
        is_valid, error = self.safety_checker.validate_strategy_parameters(strategy)
        if not is_valid:
            raise ValueError(error)
        
        self.active_strategy = strategy
        logger.info(f"✅ Strategy applied: {strategy.get('name', 'Custom')}")
    
    def get_active_strategy(self) -> Optional[Dict]:
        """Get currently active strategy"""
        return self.active_strategy
    
    async def get_status(self) -> Dict:
        """Get current engine status"""
        balance = await self.exchange_client.fetch_balance() if self.exchange_client else {'total': 0}
        
        return {
            'is_running': self.is_running,
            'exchange': settings.EXCHANGE,
            'symbol': settings.DEFAULT_SYMBOL,
            'balance': balance['total'],
            'open_positions': len(self.open_positions),
            'total_trades': self.trade_count,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_pnl': self.total_pnl,
            'uptime': (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        }
    
    async def get_open_positions(self) -> List[Dict]:
        """Get open positions"""
        return list(self.open_positions.values())
    
    async def get_balance(self) -> Dict:
        """Get account balance"""
        return await self.exchange_client.fetch_balance()


# Export
__all__ = ['HybridTradingEngine']
