"""
Base Exchange Client
Abstract base class for exchange implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd


class BaseExchangeClient(ABC):
    """Abstract base class for exchange clients"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.exchange = None
        self.exchange_name = ""
    
    @abstractmethod
    async def initialize(self):
        """Initialize exchange connection"""
        pass
    
    @abstractmethod
    async def fetch_balance(self) -> Dict[str, Any]:
        """
        Fetch account balance
        
        Returns:
            Dict with balance information
        """
        pass
    
    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "5m",
        limit: int = 200
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT:USDT')
            timeframe: Timeframe (e.g., '5m', '1h')
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        pass
    
    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch current ticker
        
        Args:
            symbol: Trading pair
            
        Returns:
            Dict with ticker data (last, bid, ask, etc.)
        """
        pass
    
    @abstractmethod
    async def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create market order
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Order amount
            params: Additional parameters (leverage, position side, etc.)
            
        Returns:
            Order details
        """
        pass
    
    @abstractmethod
    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create limit order
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Order amount
            price: Limit price
            params: Additional parameters
            
        Returns:
            Order details
        """
        pass
    
    @abstractmethod
    async def create_stop_loss_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        stop_price: float,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create stop loss order
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Order amount
            stop_price: Stop loss trigger price
            params: Additional parameters
            
        Returns:
            Order details
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Cancel order
        
        Args:
            order_id: Order ID
            symbol: Trading pair
            
        Returns:
            Cancellation result
        """
        pass
    
    @abstractmethod
    async def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Fetch open orders
        
        Args:
            symbol: Trading pair (optional, None for all)
            
        Returns:
            List of open orders
        """
        pass
    
    @abstractmethod
    async def fetch_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Fetch open positions
        
        Args:
            symbol: Trading pair (optional, None for all)
            
        Returns:
            List of open positions
        """
        pass
    
    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        Set leverage for symbol
        
        Args:
            symbol: Trading pair
            leverage: Leverage value
            
        Returns:
            Result of leverage setting
        """
        pass
    
    @abstractmethod
    async def fetch_my_trades(
        self,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Fetch recent trades
        
        Args:
            symbol: Trading pair (optional)
            limit: Number of trades to fetch
            
        Returns:
            List of recent trades
        """
        pass
    
    @abstractmethod
    async def close_position(
        self,
        symbol: str,
        side: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Close position
        
        Args:
            symbol: Trading pair
            side: Position side ('long' or 'short', optional)
            
        Returns:
            Result of position closure
        """
        pass
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol format for the exchange
        
        Args:
            symbol: Symbol in standard format
            
        Returns:
            Symbol in exchange-specific format
        """
        # Default implementation (override if needed)
        return symbol
    
    def standardize_ohlcv(self, raw_ohlcv: List) -> pd.DataFrame:
        """
        Convert raw OHLCV data to standardized DataFrame
        
        Args:
            raw_ohlcv: Raw OHLCV data from exchange
            
        Returns:
            Standardized DataFrame
        """
        df = pd.DataFrame(
            raw_ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Ensure numeric types
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_cols] = df[numeric_cols].astype(float)
        
        return df
    
    def calculate_position_size(
        self,
        balance: float,
        risk_pct: float,
        entry_price: float,
        stop_loss_price: float,
        leverage: int = 1
    ) -> float:
        """
        Calculate position size based on risk
        
        Args:
            balance: Account balance
            risk_pct: Risk percentage (e.g., 0.02 for 2%)
            entry_price: Entry price
            stop_loss_price: Stop loss price
            leverage: Leverage value
            
        Returns:
            Position size
        """
        risk_amount = balance * risk_pct
        price_diff = abs(entry_price - stop_loss_price)
        
        if price_diff == 0:
            return 0
        
        position_size = (risk_amount / price_diff) * leverage
        return position_size
    
    async def test_connection(self) -> bool:
        """
        Test exchange connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            await self.fetch_balance()
            return True
        except Exception:
            return False
    
    def get_exchange_name(self) -> str:
        """Get exchange name"""
        return self.exchange_name
    
    def is_testnet(self) -> bool:
        """Check if using testnet"""
        return self.testnet


# Export
__all__ = ['BaseExchangeClient']
