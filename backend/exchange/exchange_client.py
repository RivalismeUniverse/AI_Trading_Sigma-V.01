"""
Exchange Client for AI Trading SIGMA
Supports Binance Testnet and WEEX exchanges
"""
import ccxt
import ccxt.async_support as ccxt_async
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ExchangeClient:
    """
    Unified exchange client for multiple exchanges
    """
    
    def __init__(self):
        self.exchange = None
        self.exchange_name = settings.exchange_to_use
        self.config = settings.get_exchange_config()
        
    async def initialize(self):
        """Initialize exchange connection"""
        try:
            logger.info(f"Initializing {self.exchange_name} exchange...")
            
            if self.exchange_name == "binance_testnet":
                self.exchange = ccxt_async.binance({
                    'apiKey': self.config['apiKey'],
                    'secret': self.config['secret'],
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future',
                        'adjustForTimeDifference': True
                    }
                })
                
                # Set testnet URLs
                self.exchange.urls['api'] = {
                    'public': 'https://testnet.binancefuture.com/fapi/v1',
                    'private': 'https://testnet.binancefuture.com/fapi/v1',
                }
                
            elif self.exchange_name == "weex":
                # WEEX might need custom implementation
                # For now, we'll use a placeholder
                self.exchange = ccxt_async.weex({
                    'apiKey': self.config['apiKey'],
                    'secret': self.config['secret'],
                    'enableRateLimit': True,
                })
                
                if settings.is_testnet:
                    self.exchange.urls['api'] = self.exchange.urls['test']
            
            # Test connection
            await self.exchange.load_markets()
            logger.info(f"✅ Successfully connected to {self.exchange_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize {self.exchange_name}: {e}")
            raise
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '5m', limit: int = 100) -> List[List]:
        """Fetch OHLCV data"""
        try:
            # Convert symbol format if needed
            symbol = self._format_symbol(symbol)
            
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit
            )
            
            return ohlcv
            
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            return []
    
    async def create_market_order(self, symbol: str, side: str, amount: float, leverage: int = 1) -> Dict[str, Any]:
        """Create a market order"""
        try:
            symbol = self._format_symbol(symbol)
            
            # Set leverage if needed
            if leverage > 1 and hasattr(self.exchange, 'set_leverage'):
                await self.exchange.set_leverage(leverage, symbol)
            
            # Create order
            order = await self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=amount
            )
            
            logger.info(f"Created {side} market order for {symbol}: {amount}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create market order for {symbol}: {e}")
            return {}
    
    async def create_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        """Create a limit order"""
        try:
            symbol = self._format_symbol(symbol)
            
            order = await self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=amount,
                price=price
            )
            
            return order
            
        except Exception as e:
            logger.error(f"Failed to create limit order for {symbol}: {e}")
            return {}
    
    async def get_balance(self) -> Dict[str, Dict[str, float]]:
        """Get account balance"""
        try:
            balance = await self.exchange.fetch_balance()
            
            # Filter to show only non-zero balances
            filtered = {}
            for currency, info in balance.items():
                if currency in ['USDT', 'BTC', 'ETH'] or info['total'] > 0:
                    filtered[currency] = {
                        'free': info.get('free', 0),
                        'used': info.get('used', 0),
                        'total': info.get('total', 0)
                    }
            
            return filtered
            
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {'USDT': {'free': settings.initial_balance, 'used': 0, 'total': settings.initial_balance}}
    
    async def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get open positions"""
        try:
            if hasattr(self.exchange, 'fetch_positions'):
                positions = await self.exchange.fetch_positions()
                
                open_positions = []
                for pos in positions:
                    if pos.get('contracts', 0) != 0:
                        open_positions.append({
                            'symbol': pos.get('symbol'),
                            'side': pos.get('side', 'long'),
                            'amount': pos.get('contracts', 0),
                            'entry_price': pos.get('entryPrice', 0),
                            'current_price': pos.get('markPrice', pos.get('entryPrice', 0)),
                            'unrealized_pnl': pos.get('unrealizedPnl', 0),
                            'leverage': pos.get('leverage', 1)
                        })
                
                return open_positions
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get open positions: {e}")
            return []
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker data"""
        try:
            symbol = self._format_symbol(symbol)
            ticker = await self.exchange.fetch_ticker(symbol)
            
            return {
                'symbol': symbol,
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'last': ticker.get('last'),
                'volume': ticker.get('baseVolume', 0),
                'timestamp': ticker.get('timestamp')
            }
            
        except Exception as e:
            logger.error(f"Failed to get ticker for {symbol}: {e}")
            return {}
    
    async def get_order_book(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
        """Get order book"""
        try:
            symbol = self._format_symbol(symbol)
            orderbook = await self.exchange.fetch_order_book(symbol, limit)
            
            return {
                'bids': orderbook.get('bids', [])[:limit],
                'asks': orderbook.get('asks', [])[:limit],
                'timestamp': orderbook.get('timestamp')
            }
            
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            return {'bids': [], 'asks': []}
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        try:
            symbol = self._format_symbol(symbol)
            await self.exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    async def close_position(self, symbol: str, side: str, amount: float) -> bool:
        """Close a position"""
        try:
            symbol = self._format_symbol(symbol)
            
            # Determine close side (opposite of position)
            close_side = 'sell' if side == 'long' else 'buy'
            
            await self.create_market_order(
                symbol=symbol,
                side=close_side,
                amount=amount,
                leverage=1  # No leverage for closing
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to close position for {symbol}: {e}")
            return False
    
    def _format_symbol(self, symbol: str) -> str:
        """Format symbol for exchange"""
        # Remove any suffix if present
        if ':' in symbol:
            symbol = symbol.split(':')[0]
        
        # Binance uses BTC/USDT format
        if self.exchange_name == "binance_testnet":
            return symbol.replace('/', '')
        
        return symbol
    
    async def close(self):
        """Close exchange connection"""
        if self.exchange:
            await self.exchange.close()
            logger.info("Exchange connection closed")
