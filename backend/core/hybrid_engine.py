"""
Hybrid Trading Engine - Main autonomous trading loop
Combines 90% Python speed with 10% AI intelligence
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd

from config import settings
from strategies.scalping_strategy import ScalpingStrategy
from strategies.technical_indicators import TechnicalIndicators
from exchange.exchange_client import ExchangeClient
from exchange.safety_checker import SafetyChecker
from ai.bedrock_client import BedrockClient
from database.db_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class HybridTradingEngine:
    """
    Main trading engine that runs the autonomous trading loop
    """
    
    def __init__(
        self,
        exchange_client: ExchangeClient,
        ai_client: BedrockClient,
        db_manager: DatabaseManager
    ):
        self.exchange_client = exchange_client
        self.ai_client = ai_client
        self.db_manager = db_manager
        self.safety_checker = SafetyChecker(exchange_client, db_manager)
        
        # Strategy components
        self.scalping_strategy = ScalpingStrategy()
        self.technical_indicators = TechnicalIndicators()
        
        # State
        self.is_running = False
        self.active_strategy_name: Optional[str] = None
        self.active_strategy_config: Dict[str, Any] = {}
        self.trading_loop_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "daily_pnl": 0.0,
            "max_drawdown": 0.0,
            "current_drawdown": 0.0,
            "peak_balance": settings.initial_balance,
            "current_balance": settings.initial_balance
        }
        
        # Market data cache
        self.market_data_cache: Dict[str, pd.DataFrame] = {}
        
        logger.info("Hybrid Trading Engine initialized")
    
    async def start(self):
        """Start the autonomous trading engine"""
        if self.is_running:
            logger.warning("Trading engine is already running")
            return
        
        logger.info("🚀 Starting trading engine...")
        self.is_running = True
        
        # Start the main trading loop
        self.trading_loop_task = asyncio.create_task(self._trading_loop())
        
        logger.info("✅ Trading engine started successfully")
    
    async def stop(self):
        """Stop the autonomous trading engine"""
        if not self.is_running:
            logger.warning("Trading engine is not running")
            return
        
        logger.info("🛑 Stopping trading engine...")
        self.is_running = False
        
        # Cancel the trading loop task
        if self.trading_loop_task:
            self.trading_loop_task.cancel()
            try:
                await self.trading_loop_task
            except asyncio.CancelledError:
                pass
        
        # Close all open positions
        await self._close_all_positions()
        
        logger.info("✅ Trading engine stopped successfully")
    
    async def _trading_loop(self):
        """
        Main trading loop - runs every 5 seconds
        This is where the magic happens!
        """
        logger.info("🔁 Starting main trading loop (5-second interval)")
        
        try:
            while self.is_running:
                start_time = datetime.now()
                
                try:
                    # 1. Check if we have an active strategy
                    if not self.active_strategy_name:
                        logger.debug("No active strategy, waiting...")
                        await asyncio.sleep(5)
                        continue
                    
                    # 2. Fetch market data for all allowed symbols
                    await self._update_market_data()
                    
                    # 3. Analyze each symbol and generate signals
                    for symbol in settings.allowed_symbols:
                        await self._analyze_symbol(symbol)
                    
                    # 4. Manage existing positions
                    await self._manage_open_positions()
                    
                    # 5. Update performance metrics
                    await self._update_performance_metrics()
                    
                except Exception as e:
                    logger.error(f"Error in trading loop: {e}", exc_info=True)
                
                # 6. Calculate time taken and sleep to maintain 5-second interval
                elapsed = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0.1, 5 - elapsed)  # Aim for 5-second intervals
                
                await asyncio.sleep(sleep_time)
                
        except asyncio.CancelledError:
            logger.info("Trading loop cancelled")
        except Exception as e:
            logger.error(f"Trading loop crashed: {e}", exc_info=True)
            self.is_running = False
    
    async def _update_market_data(self):
        """Fetch and update market data for all symbols"""
        tasks = []
        for symbol in settings.allowed_symbols:
            tasks.append(self._fetch_symbol_data(symbol))
        
        # Fetch data concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _fetch_symbol_data(self, symbol: str):
        """Fetch OHLCV data for a specific symbol"""
        try:
            # Fetch 200 candles (5-minute each) for indicator calculation
            ohlcv = await self.exchange_client.fetch_ohlcv(
                symbol=symbol,
                timeframe='5m',
                limit=200
            )
            
            if ohlcv and len(ohlcv) > 50:  # Need enough data
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                
                self.market_data_cache[symbol] = df
                logger.debug(f"Updated market data for {symbol}: {len(df)} candles")
            else:
                logger.warning(f"Insufficient data for {symbol}")
                
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
    
    async def _analyze_symbol(self, symbol: str):
        """
        Analyze a symbol and execute trades if conditions are met
        """
        try:
            if symbol not in self.market_data_cache:
                return
            
            df = self.market_data_cache[symbol]
            if len(df) < 50:  # Need minimum data
                return
            
            # 1. Calculate all technical indicators
            indicators = await self._calculate_indicators(symbol, df)
            
            # 2. Generate trading signal based on active strategy
            signal = await self._generate_signal(symbol, df, indicators)
            
            if signal['action'] in ['BUY', 'SELL']:
                # 3. Validate with safety checker
                is_valid = await self.safety_checker.validate_trade(
                    symbol=symbol,
                    side='long' if signal['action'] == 'BUY' else 'short',
                    amount=signal.get('amount', 0),
                    leverage=settings.default_leverage
                )
                
                if is_valid:
                    # 4. Execute trade
                    await self._execute_trade(symbol, signal)
                else:
                    logger.warning(f"Trade blocked by safety checker: {symbol} {signal['action']}")
            
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {e}")
    
    async def _calculate_indicators(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate all technical indicators for a symbol"""
        try:
            # Basic indicators
            indicators = self.technical_indicators.calculate_all(df)
            
            # Monte Carlo simulation for probability
            mc_result = self.technical_indicators.monte_carlo_simulation(
                df['close'].values,
                n_simulations=settings.monte_carlo_simulations,
                n_periods=settings.monte_carlo_periods
            )
            
            indicators.update({
                'mc_probability_up': mc_result['probability_up'],
                'mc_expected_price': mc_result['expected_price'],
                'mc_confidence_bands': mc_result['confidence_bands']
            })
            
            # Advanced indicators
            gk_volatility = self.technical_indicators.garman_klass_volatility(df)
            z_score = self.technical_indicators.z_score_mean_reversion(df)
            lr_slope = self.technical_indicators.linear_regression_slope(df)
            
            indicators.update({
                'gk_volatility': gk_volatility,
                'z_score': z_score,
                'lr_slope': lr_slope
            })
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to calculate indicators for {symbol}: {e}")
            return {}
    
    async def _generate_signal(self, symbol: str, df: pd.DataFrame, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal based on strategy"""
        try:
            current_price = df['close'].iloc[-1]
            
            # Use active strategy or default scalping
            if self.active_strategy_name == "scalping":
                signal = self.scalping_strategy.generate_signal(df, indicators)
            else:
                # Default RSI-based strategy
                signal = {
                    'action': 'WAIT',
                    'confidence': 0.0,
                    'reason': 'No active strategy'
                }
                
                # Simple RSI strategy for demo
                rsi = indicators.get('rsi', 50)
                
                if rsi < settings.rsi_oversold:
                    signal = {
                        'action': 'BUY',
                        'confidence': (settings.rsi_oversold - rsi) / settings.rsi_oversold,
                        'reason': f'RSI oversold: {rsi:.1f}',
                        'price': current_price,
                        'stop_loss': current_price * 0.985,  # 1.5% stop loss
                        'take_profit': current_price * 1.03  # 3% take profit
                    }
                elif rsi > settings.rsi_overbought:
                    signal = {
                        'action': 'SELL',
                        'confidence': (rsi - settings.rsi_overbought) / (100 - settings.rsi_overbought),
                        'reason': f'RSI overbought: {rsi:.1f}',
                        'price': current_price,
                        'stop_loss': current_price * 1.015,  # 1.5% stop loss
                        'take_profit': current_price * 0.97  # 3% take profit
                    }
            
            return signal
            
        except Exception as e:
            logger.error(f"Failed to generate signal for {symbol}: {e}")
            return {'action': 'WAIT', 'confidence': 0.0, 'reason': f'Error: {str(e)}'}
    
    async def _execute_trade(self, symbol: str, signal: Dict[str, Any]):
        """Execute a trade based on signal"""
        try:
            side = 'buy' if signal['action'] == 'BUY' else 'sell'
            
            # Calculate position size using Kelly Criterion
            position_size = await self._calculate_position_size(symbol, signal)
            
            if position_size <= 0:
                logger.warning(f"Invalid position size for {symbol}: {position_size}")
                return
            
            # Execute market order
            order = await self.exchange_client.create_market_order(
                symbol=symbol,
                side=side,
                amount=position_size,
                leverage=settings.default_leverage
            )
            
            if order and order.get('status') in ['open', 'closed']:
                # Log the trade
                trade_record = {
                    'symbol': symbol,
                    'side': side,
                    'entry_price': signal.get('price', 0),
                    'amount': position_size,
                    'leverage': settings.default_leverage,
                    'stop_loss': signal.get('stop_loss'),
                    'take_profit': signal.get('take_profit'),
                    'signal_confidence': signal.get('confidence', 0),
                    'signal_reason': signal.get('reason', ''),
                    'order_id': order.get('id'),
                    'timestamp': datetime.utcnow()
                }
                
                await self.db_manager.save_trade(trade_record)
                
                logger.info(f"✅ Executed {side} order for {symbol}: {position_size} units")
                
                # Broadcast via WebSocket
                # (WebSocket manager would broadcast here)
                
            else:
                logger.error(f"Failed to execute order for {symbol}")
                
        except Exception as e:
            logger.error(f"Failed to execute trade for {symbol}: {e}")
    
    async def _calculate_position_size(self, symbol: str, signal: Dict[str, Any]) -> float:
        """Calculate optimal position size using Kelly Criterion"""
        try:
            # Get current balance
            balance = await self.exchange_client.get_balance()
            usdt_balance = balance.get('USDT', {}).get('free', settings.initial_balance)
            
            if usdt_balance <= 0:
                return 0
            
            # Kelly Criterion: f* = p - q/b
            # where p = win probability, q = loss probability, b = win/loss ratio
            
            # For demo, use signal confidence as win probability
            win_prob = signal.get('confidence', 0.5)
            loss_prob = 1 - win_prob
            
            # Assume 2:1 risk/reward ratio
            win_loss_ratio = 2.0
            
            # Kelly fraction
            kelly_fraction = win_prob - (loss_prob / win_loss_ratio)
            
            # Limit to 1/4 Kelly for safety
            kelly_fraction = max(0, min(kelly_fraction * 0.25, 0.1))
            
            # Adjust for volatility
            volatility = await self._get_symbol_volatility(symbol)
            if volatility > 0.05:  # High volatility
                kelly_fraction *= 0.5
            
            # Calculate position size
            risk_amount = usdt_balance * kelly_fraction
            position_size = risk_amount / signal.get('price', 1)
            
            # Apply maximum risk per trade
            max_risk = usdt_balance * settings.max_risk_per_trade
            max_position = max_risk / signal.get('price', 1)
            
            position_size = min(position_size, max_position)
            
            return position_size
            
        except Exception as e:
            logger.error(f"Failed to calculate position size: {e}")
            return 0
    
    async def _get_symbol_volatility(self, symbol: str) -> float:
        """Get volatility for a symbol"""
        try:
            if symbol in self.market_data_cache:
                df = self.market_data_cache[symbol]
                returns = df['close'].pct_change().dropna()
                return returns.std() * np.sqrt(365)  # Annualized
        except:
            pass
        return 0.02  # Default 2% volatility
    
    async def _manage_open_positions(self):
        """Manage open positions (check SL/TP, trailing stops)"""
        try:
            open_positions = await self.exchange_client.get_open_positions()
            
            for position in open_positions:
                await self._check_position_management(position)
                
        except Exception as e:
            logger.error(f"Failed to manage positions: {e}")
    
    async def _check_position_management(self, position: Dict[str, Any]):
        """Check and manage a single position"""
        try:
            symbol = position.get('symbol')
            side = position.get('side')
            entry_price = position.get('entry_price', 0)
            current_price = position.get('current_price', 0)
            
            if not symbol or entry_price == 0:
                return
            
            # Calculate P&L
            if side == 'long':
                pnl_percent = (current_price - entry_price) / entry_price
            else:  # short
                pnl_percent = (entry_price - current_price) / entry_price
            
            # Check for stop loss / take profit
            # (In real implementation, these would be set as orders on exchange)
            
            # For demo, just log
            if abs(pnl_percent) > 0.01:  # 1% move
                logger.debug(f"Position {symbol} {side}: {pnl_percent:.2%} P&L")
                
        except Exception as e:
            logger.error(f"Failed to check position: {e}")
    
    async def _close_all_positions(self):
        """Close all open positions"""
        try:
            open_positions = await self.exchange_client.get_open_positions()
            
            for position in open_positions:
                symbol = position.get('symbol')
                side = position.get('side')
                
                if symbol and side:
                    # Close with opposite order
                    close_side = 'sell' if side == 'long' else 'buy'
                    await self.exchange_client.create_market_order(
                        symbol=symbol,
                        side=close_side,
                        amount=position.get('amount', 0),
                        leverage=1  # No leverage for closing
                    )
                    logger.info(f"Closed position: {symbol} {side}")
                    
        except Exception as e:
            logger.error(f"Failed to close positions: {e}")
    
    async def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # Get current balance
            balance = await self.exchange_client.get_balance()
            usdt_balance = balance.get('USDT', {}).get('total', self.performance_metrics['current_balance'])
            
            # Update metrics
            self.performance_metrics['current_balance'] = usdt_balance
            
            if usdt_balance > self.performance_metrics['peak_balance']:
                self.performance_metrics['peak_balance'] = usdt_balance
                self.performance_metrics['current_drawdown'] = 0.0
            else:
                drawdown = (self.performance_metrics['peak_balance'] - usdt_balance) / self.performance_metrics['peak_balance']
                self.performance_metrics['current_drawdown'] = drawdown
                self.performance_metrics['max_drawdown'] = max(
                    self.performance_metrics['max_drawdown'],
                    drawdown
                )
            
        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")
    
    async def apply_strategy(self, strategy_name: str, config: Dict[str, Any] = None):
        """Apply a trading strategy"""
        try:
            self.active_strategy_name = strategy_name
            self.active_strategy_config = config or {}
            
            logger.info(f"Applied strategy: {strategy_name}")
            
        except Exception as e:
            logger.error(f"Failed to apply strategy: {e}")
            raise
    
    def get_available_strategies(self) -> List[Dict[str, Any]]:
        """Get list of available strategies"""
        return [
            {"name": "scalping", "description": "Advanced scalping strategy"},
            {"name": "rsi_mean_reversion", "description": "RSI-based mean reversion"},
            {"name": "momentum_trend", "description": "Momentum trend following"}
        ]
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            # Get trade history
            trades = await self.db_manager.get_trades(limit=100)
            
            # Calculate win rate
            if trades:
                winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
                win_rate = len(winning_trades) / len(trades) if trades else 0
            else:
                win_rate = 0
            
            metrics = self.performance_metrics.copy()
            metrics.update({
                'win_rate': win_rate * 100,
                'total_trades': len(trades),
                'winning_trades': len([t for t in trades if t.get('pnl', 0) > 0]),
                'losing_trades': len([t for t in trades if t.get('pnl', 0) < 0]),
                'timestamp': datetime.utcnow().isoformat()
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return self.performance_metrics
