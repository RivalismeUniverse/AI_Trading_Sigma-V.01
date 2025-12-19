"""
Hybrid Trading Engine - The Core of AI Trading SIGMA
Autonomous trading loop with Market Scanner Mode
Optimized for Multi-Asset Analysis
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
    Upgraded to Scan multiple assets from ALLOWED_SYMBOLS
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
            
            # Set leverage for all allowed symbols to be ready
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
            
        except Exception as e:
            logger.error(f"Failed to initialize engine: {e}")
            raise
    
    async def start(self):
        """Start autonomous trading"""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        logger.info("🚀 Starting autonomous trading in SCANNER MODE...")
        
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
        await self._close_all_positions()
        if self.exchange_client:
            await self.exchange_client.close()
        logger.info("✅ Engine stopped successfully")

    async def _main_loop(self):
        """
        Main trading loop - MARKET SCANNER
        Iterates through ALLOWED_SYMBOLS to find the best setup
        """
        cycle_count = 0
        
        while self.is_running:
            try:
                cycle_start = datetime.utcnow()
                symbols = settings.ALLOWED_SYMBOLS
                
                best_signal = None
                max_confidence = -1.0
                
                # LOOP SCANNER
                for symbol in symbols:
                    if not self.is_running: break
                    
                    # 1. Fetch data for current symbol
                    df = await self.exchange_client.fetch_ohlcv(
                        symbol=symbol,
                        timeframe=settings.DEFAULT_TIMEFRAME,
                        limit=200
                    )
                    
                    if df is None or df.empty:
                        continue
                    
                    # 2. Generate signal
                    signal = self.signal_manager.generate_signal(df, symbol)
                    
                    # 3. Logic to pick the best signal
                    if signal['action'] != TradeAction.WAIT:
                        logger.info(f"📡 Found {signal['action']} for {symbol} (Conf: {signal['confidence']:.2f})")
                        if signal['confidence'] > max_confidence:
                            max_confidence = signal['confidence']
                            best_signal = signal

                # 4. Execute the best pick
                if best_signal and max_confidence >= settings.MIN_CONFIDENCE:
                    logger.info(f"🔥 SCANNER PICK: {best_signal['symbol']} with score {max_confidence:.2f}")
                    await self._process_signal(best_signal)
                
                # 5. Manage existing positions & update metrics
                await self._manage_positions()
                await self._update_metrics()
                
                cycle_time = (datetime.utcnow() - cycle_start).total_seconds()
                cycle_count += 1
                
                if cycle_count % 5 == 0:
                    logger.info(f"✅ Scanner Cycle #{cycle_count} completed in {cycle_time*1000:.0f}ms")
                
                await asyncio.sleep(settings.TRADE_CYCLE_SECONDS)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
    
    async def _process_signal(self, signal: Dict):
        """Process signal for a specific symbol"""
        symbol = signal['symbol']
        action = signal['action']
        
        # Check circuit breaker
        allowed, reason = self.circuit_breaker.check_execution_allowed(action)
        if not allowed:
            return
        
        if action in [TradeAction.ENTER_LONG, TradeAction.ENTER_SHORT]:
            # Don't open if we already have a position in THIS symbol
            if symbol in self.open_positions:
                return
            
            # Check max open positions limit
            if len(self.open_positions) >= settings.MAX_OPEN_POSITIONS:
                logger.debug("Max open positions reached")
                return

            balance_data = await self.exchange_client.fetch_balance()
            current_balance = balance_data['total']
            
            position_size = self.risk_manager.calculate_position_size(
                balance=current_balance,
                risk_pct=settings.MAX_RISK_PER_TRADE,
                entry_price=signal['current_price'],
                stop_loss_price=signal['stop_loss'],
                leverage=settings.DEFAULT_LEVERAGE
            )
            
            is_valid, error = self.safety_checker.validate_trade(
                symbol=symbol,
                side='buy' if action == TradeAction.ENTER_LONG else 'sell',
                amount=position_size,
                leverage=settings.DEFAULT_LEVERAGE,
                price=signal['current_price'],
                account_balance=current_balance
            )
            
            if is_valid:
                await self._execute_trade(signal, position_size)
            else:
                logger.warning(f"Trade validation failed for {symbol}: {error}")

    async def _execute_trade(self, signal: Dict, position_size: float):
        """Execute market order and stop loss"""
        try:
            symbol = signal['symbol']
            action = signal['action']
            side = 'buy' if action == TradeAction.ENTER_LONG else 'sell'
            
            order = await self.exchange_client.create_market_order(
                symbol=symbol,
                side=side,
                amount=position_size,
                params={'leverage': settings.DEFAULT_LEVERAGE}
            )
            
            stop_side = 'sell' if action == TradeAction.ENTER_LONG else 'buy'
            stop_order = await self.exchange_client.create_stop_loss_order(
                symbol=symbol,
                side=stop_side,
                amount=position_size,
                stop_price=signal['stop_loss'],
                params={'reduceOnly': True}
            )
            
            self.open_positions[symbol] = {
                'entry_order': order,
                'stop_order': stop_order,
                'signal': signal,
                'entry_time': datetime.utcnow(),
                'entry_price': signal['current_price'],
                'position_size': position_size,
                'side': action
            }
            
            self.trade_count += 1
            self.db_manager.save_trade({
                'symbol': symbol,
                'action': action,
                'entry_price': signal['current_price'],
                'position_size': position_size,
                'timestamp': datetime.utcnow()
            })
            
            logger.info(f"✅ Trade #{self.trade_count} opened on {symbol}")
            
        except Exception as e:
            logger.error(f"Execution failed for {symbol}: {e}")

    async def _manage_positions(self):
        """Manage all open positions from the scanner"""
        for symbol, position in list(self.open_positions.items()):
            try:
                # Basic TP check
                ticker = await self.exchange_client.fetch_ticker(symbol)
                current_price = ticker['last']
                signal = position['signal']
                
                should_close = False
                if position['side'] == TradeAction.ENTER_LONG and current_price >= signal['take_profit']:
                    should_close = True
                elif position['side'] == TradeAction.ENTER_SHORT and current_price <= signal['take_profit']:
                    should_close = True
                
                if should_close:
                    await self._close_position(symbol, "take_profit")
                
                # Check if position still exists on exchange
                ex_pos = await self.exchange_client.fetch_positions(symbol)
                if not ex_pos:
                    await self._close_position_record(symbol, position, "stop_loss_or_manual")

            except Exception as e:
                logger.error(f"Position management error ({symbol}): {e}")

    async def _close_position(self, symbol: str, reason: str):
        try:
            await self.exchange_client.close_position(symbol)
            if symbol in self.open_positions:
                await self._close_position_record(symbol, self.open_positions[symbol], reason)
        except Exception as e:
            logger.error(f"Close error: {e}")

    async def _close_position_record(self, symbol: str, position: Dict, reason: str):
        # Simplified P&L update for the scanner
        if symbol in self.open_positions:
            del self.open_positions[symbol]
            logger.info(f"📊 Position {symbol} closed ({reason})")

    async def _update_metrics(self):
        if not self.exchange_client: return
        try:
            balance = await self.exchange_client.fetch_balance()
            current_balance = balance['total']
            self.safety_checker.record_trade({'pnl': current_balance - self.last_balance})
        except:
            pass

    async def get_status(self) -> Dict:
        # Check if exchange_client exists before calling it
        balance_val = 0
        if self.exchange_client:
            try:
                b = await self.exchange_client.fetch_balance()
                balance_val = b['total']
            except: pass
            
        return {
            'is_running': self.is_running,
            'exchange': settings.EXCHANGE,
            'balance': balance_val,
            'open_positions': len(self.open_positions),
            'total_trades': self.trade_count,
            'uptime': (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
        }

    async def get_balance(self) -> Dict:
        if not self.exchange_client: return {'total': 0, 'free': 0}
        return await self.exchange_client.fetch_balance()