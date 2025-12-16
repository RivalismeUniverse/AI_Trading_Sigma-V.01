"""
WEEX Exchange Client
Implementation for WEEX (WOO X) exchange
"""

import ccxt.async_support as ccxt
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime

from .base_client import BaseExchangeClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class WEEXClient(BaseExchangeClient):
    """WEEX Exchange Client using CCXT"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = True,
        base_url: Optional[str] = None
    ):
        super().__init__(api_key, api_secret, testnet)
        self.exchange_name = "WEEX"
        self.base_url = base_url
        
    async def initialize(self):
        """Initialize WEEX exchange connection"""
        try:
            # Initialize CCXT exchange
            self.exchange = ccxt.woo({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'swap',  # Perpetual futures
                }
            })
            
            # Set testnet if enabled
            if self.testnet:
                self.exchange.set_sandbox_mode(True)
                if self.base_url:
                    self.exchange.urls['api'] = self.base_url
            
            # Load markets
            await self.exchange.load_markets()
            
            logger.info(f"WEEX client initialized (testnet={self.testnet})")
            
        except Exception as e:
            logger.error(f"Failed to initialize WEEX client: {e}")
            raise
    
    async def fetch_balance(self) -> Dict[str, Any]:
        """Fetch account balance"""
        try:
            balance = await self.exchange.fetch_balance()
            
            # Extract relevant information
            total_balance = balance.get('USDT', {}).get('total', 0)
            free_balance = balance.get('USDT', {}).get('free', 0)
            used_balance = balance.get('USDT', {}).get('used', 0)
            
            return {
                'total': total_balance,
                'free': free_balance,
                'used': used_balance,
                'currency': 'USDT',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            raise
    
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "5m",
        limit: int = 200
    ) -> pd.DataFrame:
        """Fetch OHLCV data"""
        try:
            # Fetch raw OHLCV
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                limit=limit
            )
            
            # Standardize format
            df = self.standardize_ohlcv(ohlcv)
            
            logger.debug(f"Fetched {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            raise
    
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch current ticker"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            
            return {
                'symbol': symbol,
                'last': ticker.get('last'),
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'high': ticker.get('high'),
                'low': ticker.get('low'),
                'volume': ticker.get('volume'),
                'timestamp': ticker.get('timestamp')
            }
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            raise
    
    async def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create market order"""
        try:
            params = params or {}
            
            order = await self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=amount,
                params=params
            )
            
            logger.info(f"Market order created: {side} {amount} {symbol}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create market order: {e}")
            raise
    
    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create limit order"""
        try:
            params = params or {}
            
            order = await self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=amount,
                price=price,
                params=params
            )
            
            logger.info(f"Limit order created: {side} {amount} {symbol} @ {price}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create limit order: {e}")
            raise
    
    async def create_stop_loss_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        stop_price: float,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create stop loss order"""
        try:
            params = params or {}
            params['stopPrice'] = stop_price
            
            order = await self.exchange.create_order(
                symbol=symbol,
                type='stop_market',
                side=side,
                amount=amount,
                params=params
            )
            
            logger.info(f"Stop loss created: {side} {amount} {symbol} @ {stop_price}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create stop loss order: {e}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel order"""
        try:
            result = await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {order_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    async def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Fetch open orders"""
        try:
            orders = await self.exchange.fetch_open_orders(symbol)
            logger.debug(f"Fetched {len(orders)} open orders")
            return orders
        except Exception as e:
            logger.error(f"Failed to fetch open orders: {e}")
            raise
    
    async def fetch_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """Fetch open positions"""
        try:
            positions = await self.exchange.fetch_positions(symbol)
            
            # Filter out positions with zero size
            active_positions = [
                pos for pos in positions
                if float(pos.get('contracts', 0)) > 0
            ]
            
            logger.debug(f"Fetched {len(active_positions)} active positions")
            return active_positions
            
        except Exception as e:
            logger.error(f"Failed to fetch positions: {e}")
            raise
    
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for symbol"""
        try:
            result = await self.exchange.set_leverage(leverage, symbol)
            logger.info(f"Leverage set to {leverage}x for {symbol}")
            return result
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            raise
    
    async def fetch_my_trades(
        self,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Fetch recent trades"""
        try:
            trades = await self.exchange.fetch_my_trades(symbol, limit=limit)
            logger.debug(f"Fetched {len(trades)} trades")
            return trades
        except Exception as e:
            logger.error(f"Failed to fetch trades: {e}")
            raise
    
    async def close_position(
        self,
        symbol: str,
        side: Optional[str] = None
    ) -> Dict[str, Any]:
        """Close position"""
        try:
            # Fetch current position
            positions = await self.fetch_positions(symbol)
            
            if not positions:
                logger.warning(f"No position found for {symbol}")
                return {"status": "no_position"}
            
            position = positions[0]
            position_side = position.get('side')
            amount = abs(float(position.get('contracts', 0)))
            
            # Determine close side (opposite of position)
            close_side = 'sell' if position_side == 'long' else 'buy'
            
            # Close position with market order
            result = await self.create_market_order(
                symbol=symbol,
                side=close_side,
                amount=amount,
                params={'reduceOnly': True}
            )
            
            logger.info(f"Position closed: {symbol} {position_side}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            raise
    
    async def close(self):
        """Close exchange connection"""
        if self.exchange:
            await self.exchange.close()
            logger.info("WEEX client connection closed")


# Export
__all__ = ['WEEXClient']
