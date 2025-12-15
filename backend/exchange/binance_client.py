"""
Binance Exchange Client for WEEX Hackathon Demo
Complete implementation using CCXT with testnet support
"""

import ccxt
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class BinanceClient:
    """Binance exchange client wrapper for hackathon demo"""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = True,
        default_type: str = 'future'
    ):
        """
        Initialize Binance client
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet (True) or mainnet (False)
            default_type: 'spot', 'future', or 'margin'
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.default_type = default_type
        
        # Initialize CCXT exchange
        exchange_config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': default_type,
                'adjustForTimeDifference': True,
                'recvWindow': 60000,  # 60 seconds
            }
        }
        
        # Configure for testnet if needed
        if testnet:
            exchange_config['options']['test'] = True
            if default_type == 'future':
                # Binance Futures Testnet
                exchange_config['urls'] = {
                    'api': {
                        'public': 'https://testnet.binancefuture.com/fapi/v1',
                        'private': 'https://testnet.binancefuture.com/fapi/v1'
                    }
                }
            else:
                # Binance Spot Testnet
                exchange_config['urls'] = {
                    'api': {
                        'public': 'https://testnet.binance.vision/api/v3',
                        'private': 'https://testnet.binance.vision/api/v3'
                    }
                }
        
        self.exchange = ccxt.binance(exchange_config)
        
        logger.info(f"Binance Client initialized (Testnet: {testnet}, Type: {default_type})")
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol from WEEX format to Binance format
        
        Args:
            symbol: WEEX format symbol (e.g., 'BTC/USDT:USDT')
            
        Returns:
            Binance format symbol (e.g., 'BTC/USDT')
        """
        # Remove :USDT suffix if present
        if ':USDT' in symbol:
            symbol = symbol.replace(':USDT', '')
        
        # Ensure proper format for Binance
        # Binance uses BTC/USDT, not BTC/USDT:USDT
        return symbol
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '5m',
        limit: int = 200,
        since: Optional[int] = None
    ) -> List[List[float]]:
        """
        Fetch OHLCV data from Binance
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe string (1m, 5m, 15m, 1h, etc.)
            limit: Number of candles to fetch
            since: Timestamp in milliseconds (optional)
            
        Returns:
            List of OHLCV candles [[timestamp, open, high, low, close, volume], ...]
        """
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            candles = self.exchange.fetch_ohlcv(
                normalized_symbol, 
                timeframe, 
                limit=limit, 
                since=since
            )
            logger.debug(f"Fetched {len(candles)} {timeframe} candles for {normalized_symbol}")
            return candles
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return []
    
    def get_balance(self, currency: str = 'USDT') -> Optional[Dict[str, float]]:
        """
        Get account balance
        
        Args:
            currency: Currency to check (USDT, BTC, etc.)
            
        Returns:
            Dictionary with free, used, total balances
        """
        try:
            balance = self.exchange.fetch_balance()
            
            # Extract specific currency balance
            if currency in balance:
                currency_balance = balance[currency]
                return {
                    'free': currency_balance.get('free', 0),
                    'used': currency_balance.get('used', 0),
                    'total': currency_balance.get('total', 0)
                }
            else:
                # If currency not found, return zeros
                return {
                    'free': 0,
                    'used': 0,
                    'total': 0
                }
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return None
    
    def create_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        leverage: float = 1.0,
        params: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create market order on Binance
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Order amount in base currency
            leverage: Leverage multiplier (for futures)
            params: Additional parameters
            
        Returns:
            Order details or None if failed
        """
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            
            # For futures, set leverage if > 1
            if self.default_type == 'future' and leverage > 1.0:
                try:
                    self.exchange.set_leverage(leverage, normalized_symbol)
                except Exception as e:
                    logger.warning(f"Could not set leverage: {e}")
            
            # Create order
            order_params = params or {}
            if self.default_type == 'future':
                order_params['type'] = 'MARKET'
            
            order = self.exchange.create_order(
                symbol=normalized_symbol,
                type='market',
                side=side,
                amount=quantity,
                params=order_params
            )
            
            logger.info(f"Market order created: {side} {quantity} {normalized_symbol}")
            return order
        except Exception as e:
            logger.error(f"Error creating market order: {e}")
            return None
    
    def create_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        leverage: float = 1.0,
        params: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create limit order on Binance
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Order amount
            price: Limit price
            leverage: Leverage multiplier
            params: Additional parameters
            
        Returns:
            Order details or None if failed
        """
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            
            # For futures, set leverage if > 1
            if self.default_type == 'future' and leverage > 1.0:
                try:
                    self.exchange.set_leverage(leverage, normalized_symbol)
                except Exception as e:
                    logger.warning(f"Could not set leverage: {e}")
            
            # Create order
            order_params = params or {}
            if self.default_type == 'future':
                order_params['type'] = 'LIMIT'
                order_params['timeInForce'] = 'GTC'  # Good Till Cancelled
            
            order = self.exchange.create_order(
                symbol=normalized_symbol,
                type='limit',
                side=side,
                amount=quantity,
                price=price,
                params=order_params
            )
            
            logger.info(f"Limit order created: {side} {quantity} {normalized_symbol} @ ${price}")
            return order
        except Exception as e:
            logger.error(f"Error creating limit order: {e}")
            return None
    
    def create_stop_loss_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
        params: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create stop loss order on Binance
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Order amount
            stop_price: Stop trigger price
            params: Additional parameters
            
        Returns:
            Order details or None if failed
        """
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            
            order_params = params or {}
            order_params['stopPrice'] = stop_price
            
            if self.default_type == 'future':
                # Binance Futures stop order
                order_params['type'] = 'STOP_MARKET'
                order = self.exchange.create_order(
                    symbol=normalized_symbol,
                    type='stop_market',
                    side=side,
                    amount=quantity,
                    params=order_params
                )
            else:
                # Binance Spot stop order
                order = self.exchange.create_order(
                    symbol=normalized_symbol,
                    type='stop_loss_limit',
                    side=side,
                    amount=quantity,
                    price=stop_price * 0.99,  # Slightly below stop for execution
                    stopPrice=stop_price,
                    params=order_params
                )
            
            logger.info(f"Stop loss created: {side} {quantity} {normalized_symbol} @ ${stop_price}")
            return order
        except Exception as e:
            logger.error(f"Error creating stop loss: {e}")
            return None
    
    def create_take_profit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        params: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create take profit order on Binance
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Order amount
            price: Take profit price
            params: Additional parameters
            
        Returns:
            Order details or None if failed
        """
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            
            order_params = params or {}
            order_params['stopPrice'] = price
            
            if self.default_type == 'future':
                # Binance Futures take profit order
                order_params['type'] = 'TAKE_PROFIT_MARKET'
                order = self.exchange.create_order(
                    symbol=normalized_symbol,
                    type='take_profit_market',
                    side=side,
                    amount=quantity,
                    params=order_params
                )
            else:
                # Binance Spot take profit order
                order = self.exchange.create_order(
                    symbol=normalized_symbol,
                    type='take_profit_limit',
                    side=side,
                    amount=quantity,
                    price=price * 1.01,  # Slightly above target for execution
                    stopPrice=price,
                    params=order_params
                )
            
            logger.info(f"Take profit created: {side} {quantity} {normalized_symbol} @ ${price}")
            return order
        except Exception as e:
            logger.error(f"Error creating take profit: {e}")
            return None
    
    def cancel_order(
        self,
        order_id: str,
        symbol: str
    ) -> bool:
        """
        Cancel order on Binance
        
        Args:
            order_id: Exchange order ID
            symbol: Trading pair
            
        Returns:
            True if successful
        """
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            result = self.exchange.cancel_order(order_id, normalized_symbol)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def fetch_order(
        self,
        order_id: str,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch order details from Binance
        
        Args:
            order_id: Exchange order ID
            symbol: Trading pair
            
        Returns:
            Order details or None if failed
        """
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            order = self.exchange.fetch_order(order_id, normalized_symbol)
            return order
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            return None
    
    def fetch_open_orders(
        self,
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch open orders from Binance
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of open orders
        """
        try:
            if symbol:
                normalized_symbol = self.normalize_symbol(symbol)
                orders = self.exchange.fetch_open_orders(normalized_symbol)
            else:
                orders = self.exchange.fetch_open_orders()
            
            return orders
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []
    
    def fetch_positions(
        self,
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch open positions from Binance (futures only)
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of positions
        """
        if self.default_type != 'future':
            logger.warning("Positions only available for futures trading")
            return []
        
        try:
            positions = self.exchange.fetch_positions(symbols=[symbol] if symbol else None)
            
            # Filter only open positions
            open_positions = [
                pos for pos in positions 
                if pos.get('contracts', 0) != 0 and pos.get('notional', 0) != 0
            ]
            
            return open_positions
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []
    
    def close_position(
        self,
        symbol: str,
        side: Optional[str] = None,
        amount: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Close position on Binance (futures only)
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell' (opposite of current position)
            amount: Amount to close (None = close all)
            
        Returns:
            Order details or None if failed
        """
        if self.default_type != 'future':
            logger.warning("Position closing only available for futures")
            return None
        
        try:
            # Fetch current position
            positions = self.fetch_positions(symbol)
            if not positions:
                logger.warning(f"No open position for {symbol}")
                return None
            
            position = positions[0]
            current_side = position.get('side', 'long')
            current_amount = position.get('contracts', 0)
            
            # Determine close side (opposite of current)
            close_side = 'sell' if current_side == 'long' else 'buy'
            
            # Use provided side or calculated one
            if side and side != close_side:
                logger.warning(f"Provided side {side} doesn't match needed side {close_side}")
            
            # Use provided amount or full position
            close_amount = amount if amount is not None else current_amount
            
            # Create market order to close
            order = self.create_market_order(
                symbol=symbol,
                side=close_side,
                amount=close_amount
            )
            
            logger.info(f"Position closed: {close_side} {close_amount} {symbol}")
            return order
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return None
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker data from Binance
        
        Args:
            symbol: Trading pair
            
        Returns:
            Ticker data or None if failed
        """
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            ticker = self.exchange.fetch_ticker(normalized_symbol)
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return None
    
    def get_funding_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get funding rate for futures (Binance futures only)
        
        Args:
            symbol: Trading pair
            
        Returns:
            Funding rate data or None if failed
        """
        if self.default_type != 'future':
            logger.warning("Funding rate only available for futures")
            return None
        
        try:
            normalized_symbol = self.normalize_symbol(symbol)
            
            # Binance uses different endpoint for funding rate
            # Using CCXT's unified method
            markets = self.exchange.load_markets()
            market = markets.get(normalized_symbol)
            
            if market and 'swap' in market:
                # Fetch funding rate
                response = self.exchange.fetch_funding_rate(normalized_symbol)
                return response
            else:
                logger.warning(f"Symbol {normalized_symbol} not found or not a futures market")
                return None
        except Exception as e:
            logger.error(f"Error fetching funding rate: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test Binance connection
        
        Returns:
            True if connection successful
        """
        try:
            # Try to fetch ticker
            ticker = self.get_ticker('BTC/USDT')
            if ticker:
                logger.info(f"Connection test successful. BTC price: ${ticker.get('last', 0)}")
                return True
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_exchange_info(self) -> Optional[Dict[str, Any]]:
        """
        Get exchange information including rate limits and symbols
        
        Returns:
            Exchange info or None if failed
        """
        try:
            # Load markets to get exchange info
            markets = self.exchange.load_markets()
            
            # Get rate limits
            rate_limits = self.exchange.rateLimit
            
            return {
                'markets_count': len(markets),
                'rate_limits': rate_limits,
                'has': self.exchange.has,
                'timeframes': self.exchange.timeframes
            }
        except Exception as e:
            logger.error(f"Error getting exchange info: {e}")
            return None


# Quick test function
def test_binance_client():
    """Test the Binance client"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    print("Testing Binance Client...")
    
    # Use testnet credentials from environment or use dummy for test
    api_key = os.getenv('BINANCE_API_KEY', 'test_key')
    api_secret = os.getenv('BINANCE_API_SECRET', 'test_secret')
    
    client = BinanceClient(
        api_key=api_key,
        api_secret=api_secret,
        testnet=True,
        default_type='future'  # Use futures for leverage
    )
    
    # Test connection
    if client.test_connection():
        print("✅ Binance connection successful")
        
        # Test OHLCV
        candles = client.fetch_ohlcv('BTC/USDT:USDT', '5m', 10)
        print(f"✅ Fetched {len(candles)} candles")
        
        # Test ticker
        ticker = client.get_ticker('BTC/USDT:USDT')
        if ticker:
            print(f"✅ Ticker: ${ticker.get('last', 0)}")
        
        # Test balance
        balance = client.get_balance('USDT')
        if balance:
            print(f"✅ Balance: ${balance['total']:.2f}")
    else:
        print("❌ Binance connection failed")
    
    return client


if __name__ == '__main__':
    test_binance_client()
