import ccxt.async_support as ccxt
from typing import Dict, List, Optional, Any
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
        self.base_url = base_url
        self.exchange = None
        
    async def initialize(self):
        """Inisialisasi koneksi asli ke server WEEX menggunakan API Key & Passphrase"""
        try:
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'password': self.passphrase, # Passphrase dimasukkan ke field 'password' di CCXT
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'} # Untuk trading futures/perp sesuai guide
            }
            
            # Menggunakan driver bitget karena struktur API WEEX kompatibel
            self.exchange = ccxt.bitget(config)
            
            # Paksa gunakan sandbox jika mode testnet aktif
            if self.testnet:
                self.exchange.set_sandbox_mode(True)
            
            # Validasi koneksi dengan meload market asli
            await self.exchange.load_markets()
            
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

    async def fetch_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """Cek posisi yang sedang terbuka di akun WEEX"""
        try:
            positions = await self.exchange.fetch_positions(symbol)
            return [p for p in positions if float(p.get('contracts', 0)) > 0]
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    async def close(self):
        """Menutup koneksi API"""
        if self.exchange:
            await self.exchange.close()
