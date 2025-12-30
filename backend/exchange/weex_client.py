# backend/exchange/weex_client.py - FIXED VERSION
import ccxt.async_support as ccxt
import hashlib
import hmac
import json
import time
import aiohttp
from typing import Dict, List, Optional, Any, Union
import pandas as pd
from datetime import datetime
from .base_client import BaseExchangeClient
from utils.logger import setup_logger
import os

logger = setup_logger(__name__)


class WEEXClient(BaseExchangeClient):
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True, base_url: Optional[str] = None):
        # Inisialisasi dasar
        super().__init__(api_key, api_secret, testnet)
        self.exchange_name = "WEEX"
        
        # ✅ FIXED: Ambil passphrase dari .env dengan validasi
        self.passphrase = os.getenv('WEEX_PASSPHRASE')
        
        self.base_url = base_url or "https://api-contract.weex.com"
        self.exchange = None
        self.session = None
        
    async def initialize(self):
        """Inisialisasi koneksi asli ke server WEEX menggunakan API Key & Passphrase"""
        try:
            # ✅ FIXED: Validasi passphrase SEBELUM inisialisasi
            if not self.passphrase:
                error_msg = (
                    "❌ WEEX_PASSPHRASE tidak ditemukan di .env!\n"
                    "Passphrase wajib untuk WEEX API V2.\n"
                    "Cara fix:\n"
                    "1. Buka file backend/.env\n"
                    "2. Tambahkan baris: WEEX_PASSPHRASE=your_passphrase_here\n"
                    "3. Restart backend\n"
                    "\nCara dapatkan passphrase:\n"
                    "- Login ke WEEX account\n"
                    "- Buka API Management\n"
                    "- Saat generate API key, kamu isi passphrase sendiri\n"
                    "- Copy passphrase yang kamu buat ke .env"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # ✅ Validasi API credentials
            if not self.api_key or not self.api_secret:
                raise ValueError(
                    "❌ WEEX API Key atau Secret tidak ditemukan!\n"
                    "Pastikan WEEX_API_KEY dan WEEX_API_SECRET ada di .env"
                )
            
            logger.info("🔄 Initializing WEEX client...")
            
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'password': self.passphrase,  # Passphrase dimasukkan ke field 'password' di CCXT
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'}
            }
            
            # Menggunakan driver bitget karena struktur API WEEX kompatibel
            self.exchange = ccxt.bitget(config)
            
            # Paksa gunakan sandbox jika mode testnet aktif
            if self.testnet:
                self.exchange.set_sandbox_mode(True)
                self.base_url = "https://api-demo.weex.com"
                logger.info("🧪 Using WEEX Testnet")
            else:
                logger.info("🔴 Using WEEX Mainnet (LIVE TRADING!)")
            
            # Validasi koneksi dengan meload market asli
            logger.info("🔄 Loading markets...")
            await self.exchange.load_markets()
            logger.info(f"✅ Loaded {len(self.exchange.markets)} markets")
            
            # ✅ FIXED: Test balance untuk memastikan API key valid
            logger.info("🔄 Testing connection with balance fetch...")
            test_balance = await self.fetch_balance()
            
            balance_usd = test_balance['total']
            logger.info(f"✅ WEEX Connected Successfully!")
            logger.info(f"💰 Account Balance: ${balance_usd:.2f} USDT")
            
            if balance_usd == 0:
                logger.warning(
                    "⚠️ WARNING: Balance is $0!\n"
                    "Jika ini testnet, pastikan kamu sudah claim testnet funds:\n"
                    "1. Login ke https://testnet.weex.com\n"
                    "2. Cari menu 'Faucet' atau 'Get Test Funds'\n"
                    "3. Claim free testnet USDT"
                )
            
            # Inisialisasi HTTP session untuk API calls manual
            self.session = aiohttp.ClientSession()
            
            logger.info(f"✅ WEEX Client Initialized (Testnet={self.testnet})")
            
        except ValueError as ve:
            # Error validasi passphrase
            logger.error(str(ve))
            raise
            
        except ccxt.AuthenticationError as auth_err:
            error_msg = (
                f"❌ WEEX Authentication Failed: {auth_err}\n"
                "Kemungkinan penyebab:\n"
                "1. API Key salah\n"
                "2. API Secret salah\n"
                "3. Passphrase salah\n"
                "4. API Key tidak aktif\n"
                "5. API Key untuk mainnet tapi pakai testnet URL (atau sebaliknya)\n"
                "\nCara fix:\n"
                "1. Cek kembali WEEX_API_KEY, WEEX_API_SECRET, WEEX_PASSPHRASE di .env\n"
                "2. Pastikan API key match dengan WEEX_TESTNET setting\n"
                "3. Generate API key baru jika perlu"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        except Exception as e:
            logger.error(f"❌ WEEX Initialization Failed: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            raise

    async def fetch_balance(self) -> Dict[str, Any]:
        """Mengambil saldo ASLI dari akun WEEX"""
        try:
            if not self.exchange:
                raise Exception("Exchange not initialized. Call initialize() first.")
            
            logger.debug("📊 Fetching balance from WEEX...")
            balance = await self.exchange.fetch_balance()
            
            # ✅ FIXED: Better error handling
            usdt = balance.get('USDT', {})
            
            if not usdt:
                logger.warning(
                    "⚠️ No USDT balance found in response. "
                    "Mungkin akun belum punya balance atau currency code berbeda."
                )
            
            total = float(usdt.get('total', 0.0))
            free = float(usdt.get('free', 0.0))
            used = float(usdt.get('used', 0.0))
            
            logger.debug(f"💰 Balance: Total=${total:.2f}, Free=${free:.2f}, Used=${used:.2f}")
            
            return {
                'total': total,
                'free': free,
                'used': used,
                'currency': 'USDT',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ccxt.AuthenticationError as e:
            logger.error(f"❌ Authentication error fetching balance: {e}")
            raise Exception(f"WEEX authentication failed: {e}")
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch balance: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            raise

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Mengambil harga pasar real-time"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol, 
                'last': float(ticker.get('last', 0.0)), 
                'timestamp': ticker.get('timestamp')
            }
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {'symbol': symbol, 'last': 0.0, 'timestamp': None}

    async def create_market_order(self, symbol: str, side: str, amount: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Eksekusi Order Pasar"""
        try:
            logger.info(f"📝 Creating {side} order: {amount} {symbol}")
            order = await self.exchange.create_order(symbol, 'market', side, amount, params=params or {})
            logger.info(f"✅ Order created: {order.get('id')}")
            return order
        except Exception as e:
            logger.error(f"❌ Failed to create order: {e}")
            raise

    async def create_stop_loss_order(self, symbol: str, side: str, amount: float, stop_price: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Buat stop loss order"""
        try:
            order_params = {
                'stopPrice': stop_price,
                'reduceOnly': True
            }
            if params:
                order_params.update(params)
            
            return await self.exchange.create_order(
                symbol, 
                'stop_market' if 'stop_market' in self.exchange.options.get('orderTypes', {}) else 'market',
                side, 
                amount, 
                stop_price, 
                params=order_params
            )
        except Exception as e:
            logger.error(f"❌ Failed to create stop loss: {e}")
            raise

    async def fetch_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """Cek posisi yang sedang terbuka"""
        try:
            positions = await self.exchange.fetch_positions(symbol)
            active = [p for p in positions if float(p.get('contracts', 0)) > 0]
            logger.debug(f"📊 Active positions: {len(active)}")
            return active
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """Tutup posisi untuk simbol tertentu"""
        try:
            positions = await self.fetch_positions(symbol)
            
            if not positions:
                return {'status': 'no_position', 'symbol': symbol}
            
            position = positions[0]
            side = 'sell' if position.get('side') == 'long' else 'buy'
            amount = abs(float(position.get('contracts', 0)))
            
            order = await self.exchange.create_order(
                symbol,
                'market',
                side,
                amount,
                params={'reduceOnly': True}
            )
            
            logger.info(f"✅ Position closed for {symbol}: {amount} contracts")
            return order
            
        except Exception as e:
            logger.error(f"❌ Failed to close position for {symbol}: {e}")
            raise

    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage untuk simbol tertentu"""
        try:
            result = await self.exchange.set_leverage(leverage, symbol)
            logger.info(f"✅ Leverage set to {leverage}x for {symbol}")
            return result
        except Exception as e:
            logger.warning(f"⚠️ Leverage setting failed for {symbol}: {e}")
            return {'symbol': symbol, 'leverage': leverage, 'error': str(e)}

    async def fetch_ohlcv(self, symbol: str, timeframe: str = '5m', limit: int = 100) -> Optional[pd.DataFrame]:
        """Ambil data OHLCV untuk analisis teknikal"""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(
                ohlcv, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return None

    # ==================== AI LOGGER FUNCTIONS ====================
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """Generate signature untuk WEEX API V2 authentication"""
        message = timestamp + method.upper() + request_path + body
        
        secret = self.api_secret.encode('utf-8')
        message = message.encode('utf-8')
        
        signature = hmac.new(secret, message, hashlib.sha256).digest()
        return signature.hex()

    async def upload_ai_log(
        self,
        orderId: Optional[str] = None,
        stage: str = "Decision Making",
        model: str = "Gemini-Sigma-V.01",
        input: Optional[Dict[str, Any]] = None,
        output: Optional[Dict[str, Any]] = None,
        explanation: str = ""
    ) -> Dict[str, Any]:
        """Upload AI log ke WEEX API"""
        try:
            if not stage or not model:
                raise ValueError("Stage dan Model harus diisi")
            
            if input is None:
                input = {"prompt": "Default trading analysis", "data": {}}
            
            if output is None:
                output = {"signal": "WAIT", "confidence": 0.5, "reason": "No data"}
            
            if len(explanation) > 1000:
                explanation = explanation[:1000]
                logger.warning("Explanation trimmed to 1000 characters")
            
            payload = {
                "orderId": orderId,
                "stage": stage,
                "model": model,
                "input": input,
                "output": output,
                "explanation": explanation
            }
            
            payload = {k: v for k, v in payload.items() if v is not None}
            
            result = await self._make_api_request(
                method="POST",
                endpoint="/capi/v2/order/uploadAiLog",
                data=payload,
                private=True
            )
            
            if result.get('code') == '00000':
                logger.info(f"✅ AI Log uploaded: {stage}")
            else:
                logger.warning(f"⚠️ AI Log response: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ AI Log upload failed: {e}")
            return {
                "code": "ERROR",
                "msg": str(e),
                "requestTime": int(time.time() * 1000),
                "data": "upload failed"
            }

    async def _make_api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        private: bool = False
    ) -> Dict[str, Any]:
        """Helper untuk membuat request HTTP ke WEEX API"""
        if not self.session:
            raise Exception("Client not initialized. Call initialize() first.")
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "locale": "en-US"
        }
        
        if private:
            timestamp = str(int(time.time() * 1000))
            body = json.dumps(data) if data else ""
            
            signature = self._generate_signature(
                timestamp=timestamp,
                method=method,
                request_path=endpoint,
                body=body
            )
            
            headers.update({
                "ACCESS-KEY": self.api_key,
                "ACCESS-SIGN": signature,
                "ACCESS-TIMESTAMP": timestamp,
                "ACCESS-PASSPHRASE": self.passphrase
            })
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=aiohttp.ClientTimeout
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    logger.error(f"API Request failed: {response.status} - {response_data}")
                
                return response_data
                
        except Exception as e:
            logger.error(f"HTTP Request error: {e}")
            raise

    async def test_ai_log_connection(self) -> bool:
        """Test koneksi ke AI Log API WEEX"""
        try:
            test_payload = {
                "orderId": None,
                "stage": "Connection Test",
                "model": "Test-Model",
                "input": {
                    "prompt": "Test AI log connectivity",
                    "data": {"test": True}
                },
                "output": {
                    "signal": "TEST",
                    "confidence": 1.0,
                    "reason": "Connection test successful"
                },
                "explanation": "This is a connection test for WEEX AI Log API"
            }
            
            result = await self.upload_ai_log(**test_payload)
            
            if result.get('code') == '00000':
                logger.info("✅ AI Log API connection test PASSED")
                return True
            else:
                logger.error(f"❌ AI Log API test failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ AI Log API test exception: {e}")
            return False

    async def close(self):
        """Menutup koneksi API dan HTTP session"""
        try:
            if self.exchange:
                await self.exchange.close()
            
            if self.session:
                await self.session.close()
                
            logger.info("✅ WEEX Client closed successfully")
        except Exception as e:
            logger.error(f"Error closing WEEX client: {e}")

    # ==================== ADDITIONAL HELPER FUNCTIONS ====================
    
    async def fetch_recent_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Ambil recent trades untuk analysis"""
        try:
            trades = await self.exchange.fetch_my_trades(symbol, limit=limit)
            return [
                {
                    'id': t.get('id'),
                    'symbol': t.get('symbol'),
                    'side': t.get('side'),
                    'price': float(t.get('price', 0)),
                    'amount': float(t.get('amount', 0)),
                    'cost': float(t.get('cost', 0)),
                    'timestamp': t.get('timestamp'),
                    'fee': t.get('fee', {})
                }
                for t in trades
            ]
        except Exception as e:
            logger.error(f"Error fetching trades for {symbol}: {e}")
            return []

    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cek status order berdasarkan ID"""
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            return {
                'id': order.get('id'),
                'symbol': order.get('symbol'),
                'type': order.get('type'),
                'side': order.get('side'),
                'price': float(order.get('price', 0)),
                'amount': float(order.get('amount', 0)),
                'filled': float(order.get('filled', 0)),
                'remaining': float(order.get('remaining', 0)),
                'status': order.get('status'),
                'timestamp': order.get('timestamp')
            }
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            return {}
