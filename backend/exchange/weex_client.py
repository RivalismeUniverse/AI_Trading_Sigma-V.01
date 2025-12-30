# backend/exchange/weex_client.py - FIXED VERSION
import ccxt.async_support as ccxt
import hashlib
import hmac
import json
import time
import aiohttp
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
from .base_client import BaseExchangeClient
from utils.logger import setup_logger
import os

logger = setup_logger(__name__)


class WEEXClient(BaseExchangeClient):
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True, base_url: Optional[str] = None):
        super().__init__(api_key, api_secret, testnet)
        self.exchange_name = "WEEX"
        self.passphrase = os.getenv("WEEX_PASSPHRASE")
        self.base_url = base_url or "https://api-contract.weex.com"
        self.exchange = None
        self.session = None

    async def initialize(self):
        try:
            if not self.passphrase:
                raise ValueError("WEEX_PASSPHRASE tidak ditemukan di environment")

            if not self.api_key or not self.api_secret:
                raise ValueError("WEEX_API_KEY atau WEEX_API_SECRET tidak ditemukan")

            config = {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "password": self.passphrase,
                "enableRateLimit": True,
                "options": {"defaultType": "swap"},
            }

            self.exchange = ccxt.bitget(config)

            if self.testnet:
                self.exchange.set_sandbox_mode(True)
                self.base_url = "https://api-demo.weex.com"
                logger.info("🧪 Using WEEX Testnet")

            await self.exchange.load_markets()
            await self.fetch_balance()

            self.session = aiohttp.ClientSession()
            logger.info("✅ WEEX Client Initialized")

        except Exception as e:
            logger.error(f"WEEX initialization failed: {e}")
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

    async def create_market_order(self, symbol: str, side: str, amount: float, params: Optional[Dict] = None):
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
        message = f"{timestamp}{method.upper()}{request_path}{body}"
        return hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

    async def upload_ai_log(
        self,
        orderId: Optional[str] = None,
        stage: str = "Decision Making",
        model: str = "Gemini-Sigma-V.01",
        input: Optional[Dict[str, Any]] = None,
        output: Optional[Dict[str, Any]] = None,
        explanation: str = "",
    ):
        payload = {
            "orderId": orderId,
            "stage": stage,
            "model": model,
            "input": input or {},
            "output": output or {},
            "explanation": explanation[:1000],
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
        if not self.session:
            raise Exception("Client not initialized")

        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json", "locale": "en-US"}

        if private:
            timestamp = str(int(time.time() * 1000))
            body = json.dumps(data) if data else ""
            signature = self._generate_signature(
                timestamp, method, endpoint, body
            )

            headers.update(
                {
                    "ACCESS-KEY": self.api_key,
                    "ACCESS-SIGN": signature,
                    "ACCESS-TIMESTAMP": timestamp,
                    "ACCESS-PASSPHRASE": self.passphrase,
                }
            )

        async with self.session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            return await response.json()

    async def close(self):
        if self.exchange:
            await self.exchange.close()
        if self.session:
            await self.session.close()

    async def fetch_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        trades = await self.exchange.fetch_my_trades(symbol, limit=limit)
        return trades

    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        return await self.exchange.fetch_order(order_id, symbol)
