# backend/exchange/weex_client.py
"""
WEEX Client - COMPLETE FIXED VERSION for AI Wars Hackathon
100% compliant with WEEX API documentation
Author: AI Trading SIGMA Team

FIXES:
- Response code "00000" → "200" (all endpoints)
- fetch_balance() response structure (array not object)
- All endpoints tested and verified
"""

import hashlib
import hmac
import json
import time
import base64
import aiohttp
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import os

from .base_client import BaseExchangeClient
from utils.logger import setup_logger

logger = setup_logger(__name__)


class WEEXClient(BaseExchangeClient):
    """
    ✅ WEEX Exchange Client - Hackathon Ready & Fully Fixed
    
    Features:
    - Proper signature with base64 encoding
    - Complete headers with ACCESS-PASSPHRASE
    - Query string included in signature
    - Symbol conversion to cmt_* format
    - AI logging for compliance
    - Max leverage 20x enforcement
    - FIXED: All response codes check for "200"
    - FIXED: Balance response structure
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        base_url: Optional[str] = None,
        passphrase: Optional[str] = None,
    ):
        super().__init__(api_key, api_secret, testnet)
        self.exchange_name = "WEEX"
        
        # ✅ CRITICAL: Passphrase is MANDATORY
        self.passphrase = passphrase or os.getenv("WEEX_PASSPHRASE")
        if not self.passphrase:
            raise ValueError(
                "❌ WEEX_PASSPHRASE not found in environment!\n"
                "Add to .env: WEEX_PASSPHRASE=your_passphrase"
            )
        
        # ✅ Official WEEX API endpoint (NO testnet available)
        self.base_url = base_url or "https://api-contract.weex.com"
        
        # Session for HTTP requests
        self.session = None
        
        # Hackathon constraints
        self.max_leverage_hackathon = 20
        self.starting_balance = 1000  # USDT

    async def initialize(self):
        """Initialize WEEX connection and verify credentials"""
        try:
            if not self.api_key or not self.api_secret or not self.passphrase:
                raise ValueError(
                    "❌ Missing credentials! Required:\n"
                    "- WEEX_API_KEY\n"
                    "- WEEX_API_SECRET\n"
                    "- WEEX_PASSPHRASE"
                )

            # Create aiohttp session
            self.session = aiohttp.ClientSession()
            
            logger.info("🔧 WEEX Client initializing...")
            logger.info("🌐 Base URL: https://api-contract.weex.com")
            logger.info("⚠️  LIVE trading (no testnet available)")
            
            # Test connection by fetching balance
            balance = await self.fetch_balance()
            logger.info(f"✅ WEEX Client initialized successfully")
            logger.info(f"💰 Balance: ${balance['total']:.2f} USDT")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ WEEX initialization failed: {e}")
            raise

    def _generate_signature_post(
        self, 
        secret_key: str, 
        timestamp: str, 
        method: str, 
        request_path: str, 
        query_string: str, 
        body: str
    ) -> str:
        """
        ✅ Generate signature for POST requests
        Algorithm: HMAC-SHA256 + Base64 encoding
        
        Format: timestamp + METHOD + request_path + query_string + body
        """
        message = timestamp + method.upper() + request_path + query_string + str(body)
        signature = hmac.new(
            secret_key.encode(), 
            message.encode(), 
            hashlib.sha256
        ).digest()
        
        # ✅ CRITICAL: Must use base64, NOT hexdigest!
        return base64.b64encode(signature).decode()

    def _generate_signature_get(
        self, 
        secret_key: str, 
        timestamp: str, 
        method: str, 
        request_path: str, 
        query_string: str
    ) -> str:
        """
        ✅ Generate signature for GET requests
        Algorithm: HMAC-SHA256 + Base64 encoding
        
        Format: timestamp + METHOD + request_path + query_string
        """
        message = timestamp + method.upper() + request_path + query_string
        signature = hmac.new(
            secret_key.encode(), 
            message.encode(), 
            hashlib.sha256
        ).digest()
        
        # ✅ CRITICAL: Must use base64, NOT hexdigest!
        return base64.b64encode(signature).decode()

    async def _make_request_post(
        self,
        request_path: str,
        body: Dict,
        query_string: str = ""
    ) -> Dict[str, Any]:
        """✅ Send POST request to WEEX API"""
        if not self.session:
            raise Exception("❌ Client not initialized. Call initialize() first.")
        
        timestamp = str(int(time.time() * 1000))
        body_json = json.dumps(body)
        
        signature = self._generate_signature_post(
            self.api_secret, timestamp, "POST", request_path, query_string, body_json
        )
        
        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US"
        }
        
        url = f"{self.base_url}{request_path}"
        
        try:
            async with self.session.post(
                url, headers=headers, data=body_json,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = await response.json()
                
                if response.status != 200:
                    logger.error(f"❌ WEEX POST error [{response.status}]: {result}")
                    if response.status == 521:
                        logger.error("⚠️  Error 521: IP not whitelisted!")
                
                # ✅ FIXED: Check for "200" not "00000"
                if result.get("code") != "200":
                    logger.warning(f"⚠️  WEEX response code: {result.get('code')} - {result.get('msg')}")
                    
                return result
                
        except Exception as e:
            logger.error(f"❌ POST request failed: {e}")
            raise

    async def _make_request_get(
        self,
        request_path: str,
        query_string: str = ""
    ) -> Dict[str, Any]:
        """✅ Send GET request to WEEX API"""
        if not self.session:
            raise Exception("❌ Client not initialized. Call initialize() first.")
        
        timestamp = str(int(time.time() * 1000))
        
        signature = self._generate_signature_get(
            self.api_secret, timestamp, "GET", request_path, query_string
        )
        
        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US"
        }
        
        url = f"{self.base_url}{request_path}{query_string}"
        
        try:
            async with self.session.get(
                url, headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = await response.json()
                
                if response.status != 200:
                    logger.error(f"❌ WEEX GET error [{response.status}]: {result}")
                    if response.status == 521:
                        logger.error("⚠️  Error 521: IP not whitelisted!")
                
                # ✅ FIXED: Check for "200" not "00000"
                if result.get("code") != "200":
                    logger.warning(f"⚠️  WEEX response code: {result.get('code')} - {result.get('msg')}")
                    
                return result
                
        except Exception as e:
            logger.error(f"❌ GET request failed: {e}")
            raise

    def _convert_symbol(self, symbol: str) -> str:
        """Convert standard symbol format to WEEX format"""
        if ":" in symbol:
            symbol = symbol.split(":")[0]
        symbol = symbol.replace("/", "").lower()
        return f"cmt_{symbol}"

    async def fetch_balance(self) -> Dict[str, Any]:
        """
        ✅ Fetch account balance - FIXED response structure
        Endpoint: GET /capi/v2/account/assets
        """
        try:
            result = await self._make_request_get("/capi/v2/account/assets", "")
            
            # ✅ FIXED: Check for "200"
            if result.get("code") != "200":
                raise Exception(f"Balance fetch failed: {result}")
            
            # ✅ FIXED: Response is ARRAY, not object
            data_list = result.get("data", [])
            
            # Find USDT balance
            usdt_data = None
            for item in data_list:
                if item.get("coinName") == "USDT":
                    usdt_data = item
                    break
            
            if not usdt_data:
                # Return zero if no USDT found
                logger.warning("⚠️  USDT balance not found in response")
                return {
                    "total": 0.0,
                    "free": 0.0,
                    "used": 0.0,
                    "unrealized_pnl": 0.0,
                    "currency": "USDT",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            
            # Parse USDT balance
            total = float(usdt_data.get("equity", 0))
            available = float(usdt_data.get("available", 0))
            frozen = float(usdt_data.get("frozen", 0))
            unrealized_pnl = float(usdt_data.get("unrealizePnl", 0))
            
            return {
                "total": total,
                "free": available,
                "used": frozen,
                "unrealized_pnl": unrealized_pnl,
                "currency": "USDT",
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"❌ Fetch balance error: {e}")
            raise

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """✅ Fetch current ticker/price"""
        try:
            weex_symbol = self._convert_symbol(symbol)
            query = f"?symbol={weex_symbol}"
            
            result = await self._make_request_get("/capi/v2/market/ticker", query)
            
            # ✅ FIXED: Check for "200"
            if result.get("code") != "200":
                raise Exception(f"Ticker fetch failed: {result}")
            
            data = result.get("data", {})
            
            return {
                "symbol": symbol,
                "last": float(data.get("last", 0)),
                "bid": float(data.get("best_bid", 0)),
                "ask": float(data.get("best_ask", 0)),
                "high": float(data.get("high_24h", 0)),
                "low": float(data.get("low_24h", 0)),
                "volume": float(data.get("volume_24h", 0)),
                "timestamp": int(data.get("timestamp", int(time.time() * 1000))),
            }
            
        except Exception as e:
            logger.error(f"❌ Fetch ticker error: {e}")
            raise

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str = "5m", limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """✅ Fetch OHLCV (candlestick) data"""
        try:
            weex_symbol = self._convert_symbol(symbol)
            
            period_map = {
                "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
                "1h": "1h", "4h": "4h", "1d": "1d"
            }
            period = period_map.get(timeframe, "5m")
            
            query = f"?symbol={weex_symbol}&period={period}&size={limit}"
            result = await self._make_request_get("/capi/v2/market/klines", query)
            
            # ✅ FIXED: Check for "200"
            if result.get("code") != "200":
                raise Exception(f"OHLCV fetch failed: {result}")
            
            data = result.get("data", [])
            
            if not data:
                logger.warning(f"⚠️  No OHLCV data returned for {symbol}")
                return None
            
            df = pd.DataFrame(
                data, 
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df[["open", "high", "low", "close", "volume"]] = df[
                ["open", "high", "low", "close", "volume"]
            ].astype(float)
            
            df.set_index("timestamp", inplace=True)
            df["current_price"] = df["close"]
            
            logger.debug(f"✅ Fetched {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Fetch OHLCV error: {e}")
            return None

    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """✅ Set leverage for a symbol"""
        try:
            if leverage > self.max_leverage_hackathon:
                logger.warning(
                    f"⚠️  Leverage {leverage}x exceeds hackathon maximum!\n"
                    f"   Using {self.max_leverage_hackathon}x instead"
                )
                leverage = self.max_leverage_hackathon
            
            weex_symbol = self._convert_symbol(symbol)
            
            body = {
                "symbol": weex_symbol,
                "marginMode": 1,
                "longLeverage": str(leverage),
                "shortLeverage": str(leverage)
            }
            
            result = await self._make_request_post("/capi/v2/account/leverage", body)
            
            # ✅ FIXED: Check for "200"
            if result.get("code") == "200":
                logger.info(f"✅ Leverage set to {leverage}x for {symbol}")
            else:
                logger.error(f"❌ Set leverage failed: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Set leverage error: {e}")
            raise

    async def create_market_order(
        self, symbol: str, side: str, amount: float, params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """✅ Create market order"""
        try:
            weex_symbol = self._convert_symbol(symbol)
            client_oid = f"sigma_{int(time.time() * 1000000)}"
            
            body = {
                "symbol": weex_symbol,
                "client_oid": client_oid,
                "size": str(amount),
                "type": "1" if side == "buy" else "2",
                "order_type": "0",
                "match_price": "1",
                "price": "0"
            }
            
            if params:
                body.update(params)
            
            result = await self._make_request_post("/capi/v2/order/placeOrder", body)
            
            # ✅ FIXED: Check for "200"
            if result.get("code") == "200":
                order_id = result.get("data", {}).get("order_id")
                logger.info(f"✅ Market order placed: {side.upper()} {amount} {symbol} (ID: {order_id})")
            else:
                logger.error(f"❌ Order failed: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Create market order error: {e}")
            raise

    async def create_limit_order(
        self, symbol: str, side: str, amount: float, price: float, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """✅ Create limit order"""
        try:
            weex_symbol = self._convert_symbol(symbol)
            client_oid = f"sigma_{int(time.time() * 1000000)}"
            
            body = {
                "symbol": weex_symbol,
                "client_oid": client_oid,
                "size": str(amount),
                "type": "1" if side == "buy" else "2",
                "order_type": "0",
                "match_price": "0",
                "price": str(price)
            }
            
            if params:
                body.update(params)
            
            result = await self._make_request_post("/capi/v2/order/placeOrder", body)
            
            # ✅ FIXED: Check for "200"
            if result.get("code") == "200":
                order_id = result.get("data", {}).get("order_id")
                logger.info(f"✅ Limit order placed: {side.upper()} {amount} {symbol} @ ${price}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Create limit order error: {e}")
            raise

    async def create_stop_loss_order(
        self, symbol: str, side: str, amount: float, stop_price: float, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """✅ Create stop loss order"""
        try:
            weex_symbol = self._convert_symbol(symbol)
            client_oid = f"sigma_{int(time.time() * 1000000)}"
            
            body = {
                "symbol": weex_symbol,
                "client_oid": client_oid,
                "size": str(amount),
                "type": "1" if side == "buy" else "2",
                "order_type": "2",
                "trigger_price": str(stop_price),
                "price": "0"
            }
            
            if params:
                body.update(params)
            
            result = await self._make_request_post("/capi/v2/order/placeOrder", body)
            return result
            
        except Exception as e:
            logger.error(f"❌ Create stop loss error: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """✅ Cancel an order"""
        try:
            weex_symbol = self._convert_symbol(symbol)
            
            body = {"symbol": weex_symbol, "order_id": order_id}
            result = await self._make_request_post("/capi/v2/order/cancelOrder", body)
            
            # ✅ FIXED: Check for "200"
            if result.get("code") == "200":
                logger.info(f"✅ Order cancelled: {order_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Cancel order error: {e}")
            raise

    async def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """✅ Fetch open orders"""
        try:
            query = f"?symbol={self._convert_symbol(symbol)}" if symbol else ""
            result = await self._make_request_get("/capi/v2/order/currentOrders", query)
            
            # ✅ FIXED: Check for "200"
            if result.get("code") == "200":
                return result.get("data", {}).get("list", [])
            return []
            
        except Exception as e:
            logger.error(f"❌ Fetch open orders error: {e}")
            return []

    async def fetch_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """✅ Fetch open positions"""
        try:
            query = f"?symbol={self._convert_symbol(symbol)}" if symbol else ""
            result = await self._make_request_get("/capi/v2/account/position/allPosition", query)
            
            # ✅ FIXED: Check for "200"
            if result.get("code") == "200":
                positions = result.get("data", {}).get("list", [])
                return [pos for pos in positions if float(pos.get("total", 0)) > 0]
            return []
            
        except Exception as e:
            logger.error(f"❌ Fetch positions error: {e}")
            return []

    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """✅ Close position"""
        try:
            positions = await self.fetch_positions(symbol)
            
            if not positions:
                return {"status": "no_position", "symbol": symbol}
            
            position = positions[0]
            position_side = position.get("positionSide", "LONG")
            amount = abs(float(position.get("total", 0)))
            close_side = "sell" if position_side == "LONG" else "buy"
            
            result = await self.create_market_order(
                symbol=symbol, side=close_side, amount=amount,
                params={"reduceOnly": True}
            )
            
            # ✅ FIXED: Check for "200"
            if result.get("code") == "200":
                logger.info(f"✅ Position closed: {symbol} {position_side}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Close position error: {e}")
            raise

    async def fetch_my_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """✅ Fetch trade history"""
        try:
            weex_symbol = self._convert_symbol(symbol)
            query = f"?symbol={weex_symbol}&pageSize={limit}"
            result = await self._make_request_get("/capi/v2/order/fills", query)
            
            # ✅ FIXED: Check for "200"
            if result.get("code") == "200":
                return result.get("data", {}).get("list", [])
            return []
            
        except Exception as e:
            logger.error(f"❌ Fetch trades error: {e}")
            return []

    async def upload_ai_log(
        self, orderId: Optional[str] = None, stage: str = "Decision Making",
        model: str = "AI-Trading-Sigma-v1.0", input: Optional[Dict[str, Any]] = None,
        output: Optional[Dict[str, Any]] = None, explanation: str = "",
    ) -> Dict[str, Any]:
        """✅ Upload AI decision log"""
        try:
            payload = {
                "orderId": orderId,
                "stage": stage,
                "model": model,
                "input": input or {},
                "output": output or {},
                "explanation": explanation[:1000],
            }
            
            result = await self._make_request_post("/capi/v2/order/uploadAiLog", payload)
            
            # ✅ FIXED: Check for "200"
            if result.get("code") == "200":
                logger.debug(f"✅ AI log uploaded for order {orderId}")
            else:
                logger.warning(f"⚠️  AI log upload failed: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Upload AI log error: {e}")
            return {"code": "ERROR", "msg": str(e)}

    async def get_contract_info(self, symbol: str) -> Dict[str, Any]:
        """✅ Get contract information"""
        try:
            weex_symbol = self._convert_symbol(symbol)
            query = f"?symbol={weex_symbol}"
            result = await self._make_request_get("/capi/v2/market/contracts", query)
            
            # ✅ FIXED: Check for "200"
            if result.get("code") == "200":
                contracts = result.get("data", [])
                if contracts:
                    return contracts[0]
            return {}
            
        except Exception as e:
            logger.error(f"❌ Get contract info error: {e}")
            return {}

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            logger.info("✅ WEEX client session closed")

    def get_allowed_symbols_hackathon(self) -> List[str]:
        """Get list of allowed symbols for hackathon"""
        return [
            "BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT", "DOGE/USDT:USDT",
            "XRP/USDT:USDT", "ADA/USDT:USDT", "BNB/USDT:USDT", "LTC/USDT:USDT"
        ]

    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            balance = await self.fetch_balance()
            logger.info(f"✅ Connection test successful: ${balance['total']:.2f} USDT")
            return True
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False


__all__ = ['WEEXClient']
