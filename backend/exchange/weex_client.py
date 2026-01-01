# backend/exchange/weex_client.py - IMPROVED VERSION
import ccxt.async_support as ccxt
import hashlib
import hmac
import json
import time
import aiohttp
import asyncio
from functools import wraps
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
from .base_client import BaseExchangeClient
from utils.logger import setup_logger
import os

logger = setup_logger(__name__)


def retry_on_failure(max_retries=3, delay=1):
    """Decorator untuk retry API calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (attempt + 1)
                        logger.warning(f"⚠️ {func.__name__} attempt {attempt+1} failed, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"❌ {func.__name__} - All {max_retries} attempts failed")
            raise last_error
        return wrapper
    return decorator


class WEEXClient(BaseExchangeClient):
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        passphrase: str = None,  # ✅ ADDED passphrase parameter
        testnet: bool = False,
        base_url: Optional[str] = None,
    ):
        super().__init__(api_key, api_secret, testnet)
        self.exchange_name = "WEEX"
        
        # ✅ Get passphrase from parameter or environment
        self.passphrase = passphrase or os.getenv("WEEX_PASSPHRASE")
        
        # 🔥 SINGLE OFFICIAL BASE URL
        self.base_url = base_url or "https://api-contract.weex.com"
        self.exchange = None
        self.session = None

    async def initialize(self):
        try:
            # ✅ IMPROVED VALIDATION with clear error messages
            if not self.api_key:
                raise ValueError("❌ WEEX_API_KEY tidak ditemukan di environment")
            if not self.api_secret:
                raise ValueError("❌ WEEX_API_SECRET tidak ditemukan di environment")
            if not self.passphrase:
                raise ValueError("❌ WEEX_PASSPHRASE tidak ditemukan di environment")
            
            # ✅ DEBUG LOGGING (safe - only show first/last chars)
            logger.info("✅ WEEX credentials validated")
            logger.info(f"   API Key: {self.api_key[:4]}****{self.api_key[-4:]}")
            logger.info(f"   Passphrase: {self.passphrase[:2]}****")
            
            config = {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "password": self.passphrase,
                "enableRateLimit": True,
                "options": {"defaultType": "swap"},
            }
            
            # 🔥 WEEX menggunakan engine yang kompatibel dengan Bitget
            self.exchange = ccxt.bitget(config)
            logger.info("🔥 WEEX LIVE environment (no testnet available)")
            
            await self.exchange.load_markets()
            
            # ✅ Test connection dengan fetch balance
            await self.fetch_balance()
            
            self.session = aiohttp.ClientSession()
            logger.info("🔥 WEEX Client Initialized (LIVE)")
            
        except Exception as e:
            logger.error(f"🔥 WEEX initialization failed: {e}")
            raise

    async def fetch_balance(self) -> Dict[str, Any]:
        if not self.exchange:
            raise Exception("Exchange not initialized")
        
        balance = await self.exchange.fetch_balance()
        usdt = balance.get("USDT", {})
        
        return {
            "total": float(usdt.get("total", 0)),
            "free": float(usdt.get("free", 0)),
            "used": float(usdt.get("used", 0)),
            "currency": "USDT",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        ticker = await self.exchange.fetch_ticker(symbol)
        return {
            "symbol": symbol,
            "last": float(ticker.get("last", 0)),
            "timestamp": ticker.get("timestamp"),
        }

    # 🔥 ABSTRACT METHODS IMPLEMENTATION
    async def create_limit_order(self, symbol: str, side: str, amount: float, price: float, params: Optional[Dict] = None):
        return await self.exchange.create_order(symbol, 'limit', side, amount, price, params=params or {})

    async def cancel_order(self, order_id: str, symbol: str):
        return await self.exchange.cancel_order(order_id, symbol)

    async def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        return await self.exchange.fetch_open_orders(symbol)

    async def fetch_my_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        return await self.exchange.fetch_my_trades(symbol, limit=limit)

    async def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        params: Optional[Dict] = None,
    ):
        return await self.exchange.create_order(
            symbol, "market", side, amount, params=params or {}
        )

    async def create_stop_loss_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        stop_price: float,
        params: Optional[Dict] = None,
    ):
        order_params = {"stopPrice": stop_price, "reduceOnly": True}
        if params:
            order_params.update(params)
        
        return await self.exchange.create_order(
            symbol,
            "stop_market",
            side,
            amount,
            stop_price,
            params=order_params,
        )

    async def fetch_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        positions = await self.exchange.fetch_positions(symbol)
        return [p for p in positions if float(p.get("contracts", 0)) > 0]

    async def close_position(self, symbol: str):
        positions = await self.fetch_positions(symbol)
        if not positions:
            return {"status": "no_position", "symbol": symbol}
        
        pos = positions[0]
        side = "sell" if pos.get("side") == "long" else "buy"
        amount = abs(float(pos.get("contracts", 0)))
        
        return await self.exchange.create_order(
            symbol, "market", side, amount, params={"reduceOnly": True}
        )

    async def set_leverage(self, symbol: str, leverage: int):
        try:
            return await self.exchange.set_leverage(leverage, symbol)
        except Exception as e:
            return {"symbol": symbol, "leverage": leverage, "error": str(e)}

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str = "5m", limit: int = 100
    ) -> Optional[pd.DataFrame]:
        ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(
            ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df

    def _generate_signature(
        self, timestamp: str, method: str, request_path: str, body: str = ""
    ) -> str:
        """Generate HMAC SHA256 signature for WEEX API V2"""
        message = f"{timestamp}{method.upper()}{request_path}{body}"
        return hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

    @retry_on_failure(max_retries=3, delay=2)  # ✅ ADDED RETRY
    async def upload_ai_log(
        self,
        orderId: Optional[str] = None,
        stage: str = "Decision Making",
        model: str = "Gemini-Sigma-V.01",
        input: Optional[Dict[str, Any]] = None,
        output: Optional[Dict[str, Any]] = None,
        explanation: str = "",
    ):
        """
        Upload AI log to WEEX with retry mechanism
        """
        payload = {
            "orderId": orderId,
            "stage": stage,
            "model": model,
            "input": input or {},
            "output": output or {},
            "explanation": explanation[:1000],  # Max 1000 chars
        }
        
        return await self._make_api_request(
            method="POST",
            endpoint="/capi/v2/order/uploadAiLog",
            data=payload,
            private=True,
        )

    async def _make_api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        private: bool = False,
    ) -> Dict[str, Any]:
        """Make authenticated API request to WEEX"""
        if not self.session:
            raise Exception("Client not initialized")
        
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json", "locale": "en-US"}
        
        if private:
            timestamp = str(int(time.time() * 1000))
            body = json.dumps(data) if data else ""
            signature = self._generate_signature(timestamp, method, endpoint, body)
            
            headers.update({
                "ACCESS-KEY": self.api_key,
                "ACCESS-SIGN": signature,
                "ACCESS-TIMESTAMP": timestamp,
                "ACCESS-PASSPHRASE": self.passphrase,
            })
        
        async with self.session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            result = await response.json()
            
            # ✅ LOG response untuk debugging
            if result.get('code') != '00000':
                logger.warning(f"⚠️ WEEX API response: {result}")
            
            return result

    async def close(self):
        if self.exchange:
            await self.exchange.close()
        if self.session:
            await self.session.close()

    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        return await self.exchange.fetch_order(order_id, symbol)
