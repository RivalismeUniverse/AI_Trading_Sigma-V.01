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
        # Ambil passphrase dari .env (Field ini wajib untuk WEEX API V2)
        self.passphrase = os.getenv('WEEX_PASSPHRASE')
        self.base_url = base_url or "https://api-contract.weex.com"
        self.exchange = None
        self.session = None  # Untuk HTTP requests manual
        
    async def initialize(self):
        """Inisialisasi koneksi asli ke server WEEX menggunakan API Key & Passphrase"""
        try:
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'password': self.passphrase,  # Passphrase dimasukkan ke field 'password' di CCXT
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'}  # Untuk trading futures/perp sesuai guide
            }
            
            # Menggunakan driver bitget karena struktur API WEEX kompatibel
            self.exchange = ccxt.bitget(config)
            
            # Paksa gunakan sandbox jika mode testnet aktif
            if self.testnet:
                self.exchange.set_sandbox_mode(True)
                self.base_url = "https://api-demo.weex.com"  # Testnet URL
            
            # Validasi koneksi dengan meload market asli
            await self.exchange.load_markets()
            
            # Inisialisasi HTTP session untuk API calls manual
            self.session = aiohttp.ClientSession()
            
            logger.info(f"✅ WEEX Client Initialized (Testnet={self.testnet})")
        except Exception as e:
            logger.error(f"❌ WEEX Initialization Failed: {e}")
            raise

    async def fetch_balance(self) -> Dict[str, Any]:
        """Mengambil saldo ASLI (Testing 1000 USDT) dari akun WEEX"""
        try:
            balance = await self.exchange.fetch_balance()
            usdt = balance.get('USDT', {})
            
            return {
                'total': float(usdt.get('total', 0.0)),
                'free': float(usdt.get('free', 0.0)),
                'used': float(usdt.get('used', 0.0)),
                'currency': 'USDT',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"⚠️ Gagal mengambil saldo asli WEEX: {e}")
            raise e

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Mengambil harga pasar real-time untuk simulasi dan sinyal"""
        try:
            # Sesuaikan simbol jika perlu (misal: cmt_btcusdt sesuai guide)
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
        """Eksekusi Order Pasar untuk memenuhi syarat trading 10 USDT"""
        try:
            return await self.exchange.create_order(symbol, 'market', side, amount, params=params or {})
        except Exception as e:
            logger.error(f"❌ Gagal membuat order di WEEX: {e}")
            raise e

    async def create_stop_loss_order(self, symbol: str, side: str, amount: float, stop_price: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Buat stop loss order untuk proteksi posisi"""
        try:
            order_params = {
                'stopPrice': stop_price,
                'reduceOnly': True
            }
            if params:
                order_params.update(params)
            
            return await self.exchange.create_order(
                symbol, 
                'stop_market' if 'stop_market' in self.exchange.options['orderTypes'] else 'market',
                side, 
                amount, 
                stop_price, 
                params=order_params
            )
        except Exception as e:
            logger.error(f"❌ Gagal membuat stop loss di WEEX: {e}")
            raise e

    async def fetch_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """Cek posisi yang sedang terbuka di akun WEEX"""
        try:
            positions = await self.exchange.fetch_positions(symbol)
            return [p for p in positions if float(p.get('contracts', 0)) > 0]
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """Tutup posisi untuk simbol tertentu"""
        try:
            # Cari posisi yang masih terbuka
            positions = await self.fetch_positions(symbol)
            
            if not positions:
                return {'status': 'no_position', 'symbol': symbol}
            
            position = positions[0]
            side = 'sell' if position.get('side') == 'long' else 'buy'
            amount = abs(float(position.get('contracts', 0)))
            
            # Buat order untuk menutup posisi
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
            logger.error(f"❌ Gagal menutup posisi untuk {symbol}: {e}")
            raise e

    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage untuk simbol tertentu"""
        try:
            return await self.exchange.set_leverage(leverage, symbol)
        except Exception as e:
            logger.warning(f"Leverage setting failed for {symbol}: {e}")
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
        
        # Decode secret jika dalam format base64
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
        """
        Upload AI log ke WEEX API sesuai spesifikasi mereka
        POST /capi/v2/order/uploadAiLog
        
        Parameters wajib sesuai WEEX docs:
        - orderId: Long (optional)
        - stage: String (required) - e.g., "Strategy Generation", "Decision Making"
        - model: String (required) - e.g., "GPT-4-turbo"
        - input: JSON (required) - prompt + data
        - output: JSON (required) - signal + confidence + reason
        - explanation: String (required) - max 1000 chars
        """
        try:
            # Validasi parameter
            if not stage or not model:
                raise ValueError("Stage dan Model harus diisi")
            
            # Pastikan input/output format JSON yang benar
            if input is None:
                input = {"prompt": "Default trading analysis", "data": {}}
            
            if output is None:
                output = {"signal": "WAIT", "confidence": 0.5, "reason": "No data"}
            
            # Potong explanation jika terlalu panjang
            if len(explanation) > 1000:
                explanation = explanation[:1000]
                logger.warning("Explanation trimmed to 1000 characters")
            
            # Siapkan payload
            payload = {
                "orderId": orderId,
                "stage": stage,
                "model": model,
                "input": input,
                "output": output,
                "explanation": explanation
            }
            
            # Hapus null values untuk field optional
            payload = {k: v for k, v in payload.items() if v is not None}
            
            # Panggil API WEEX dengan signature yang benar
            result = await self._make_api_request(
                method="POST",
                endpoint="/capi/v2/order/uploadAiLog",
                data=payload,
                private=True
            )
            
            if result.get('code') == '00000':
                logger.info(f"✅ AI Log uploaded successfully for stage: {stage}")
            else:
                logger.warning(f"⚠️ AI Log upload response: {result}")
            
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
        """
        Helper untuk membuat request HTTP ke WEEX API dengan authentication yang benar
        """
        if not self.session:
            raise Exception("Client not initialized. Call initialize() first.")
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "locale": "en-US"
        }
        
        # Generate signature untuk private endpoints
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
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    logger.error(f"API Request failed: {response.status} - {response_data}")
                
                return response_data
                
        except Exception as e:
            logger.error(f"HTTP Request error: {e}")
            raise e

    async def test_ai_log_connection(self) -> bool:
        """
        Test koneksi ke AI Log API WEEX untuk compliance check
        Wajib dipanggil sebelum mulai trading
        """
        try:
            # Buat test payload sederhana
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
