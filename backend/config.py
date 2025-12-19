"""
Configuration Management for AI Trading SIGMA
Handles all environment variables and application settings
Optimized for Google Gemini Integration
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "AI Trading SIGMA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    
    # Google Gemini (NEW - FREE AI)
    GEMINI_API_KEY: str = Field(default="")
    
    # AWS Bedrock (Keep for compatibility, but optional now)
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    AWS_REGION: str = Field(default="us-east-1")
    BEDROCK_MODEL_ID: str = Field(default="anthropic.claude-3-5-sonnet-20241022-v2:0")
    
    # Exchange Selection
    EXCHANGE: str = Field(default="weex")  # "weex" or "binance"
    
    # WEEX Exchange
    WEEX_API_KEY: str = Field(default="")
    WEEX_API_SECRET: str = Field(default="")
    WEEX_TESTNET: bool = Field(default=True)
    WEEX_BASE_URL: Optional[str] = Field(default=None)
    
    # Binance Exchange
    BINANCE_API_KEY: str = Field(default="")
    BINANCE_API_SECRET: str = Field(default="")
    BINANCE_TESTNET: bool = Field(default=True)
    
    # Trading Settings
    DEFAULT_SYMBOL: str = Field(default="BTC/USDT:USDT")
    DEFAULT_LEVERAGE: int = Field(default=10)
    DEFAULT_TIMEFRAME: str = Field(default="5m")
    MAX_LEVERAGE: int = Field(default=20)
    
    # Risk Management
    MAX_RISK_PER_TRADE: float = Field(default=0.02)  # 2% per trade
    MAX_DAILY_LOSS: float = Field(default=0.05)  # 5% daily loss limit
    MAX_OPEN_POSITIONS: int = Field(default=3)
    KELLY_FRACTION: float = Field(default=0.25)  # Conservative Kelly
    
    # Strategy Settings
    RSI_PERIOD: int = Field(default=14)
    RSI_OVERSOLD: float = Field(default=30.0)
    RSI_OVERBOUGHT: float = Field(default=70.0)
    
    MACD_FAST: int = Field(default=12)
    MACD_SLOW: int = Field(default=26)
    MACD_SIGNAL: int = Field(default=9)
    
    BB_PERIOD: int = Field(default=20)
    BB_STD: float = Field(default=2.0)
    
    # Monte Carlo Settings
    MC_SIMULATIONS: int = Field(default=1000)
    MC_HORIZON: int = Field(default=12)  # 12 periods (1 hour for 5m)
    MC_CONFIDENCE: float = Field(default=0.65)  # 65% probability threshold
    
    # Signal Generation
    SIGNAL_LONG_THRESHOLD: float = Field(default=0.3)
    SIGNAL_SHORT_THRESHOLD: float = Field(default=0.3)
    MIN_CONFIDENCE: float = Field(default=0.33)
    
    # Execution
    TRADE_CYCLE_SECONDS: int = Field(default=5)
    ORDER_TIMEOUT: int = Field(default=30)
    MAX_SLIPPAGE: float = Field(default=0.001)  # 0.1%
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./trading_data.db")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="logs/trading_bot.log")
    COMPLIANCE_LOG_DIR: str = Field(default="logs/hackathon")
    
    # Hackathon Compliance
    ALLOWED_SYMBOLS: List[str] = Field(default=[
        'ADA/USDT:USDT',
        'SOL/USDT:USDT',
        'LTC/USDT:USDT',
        'DOGE/USDT:USDT',
        'BTC/USDT:USDT',
        'ETH/USDT:USDT',
        'XRP/USDT:USDT',
        'BNB/USDT:USDT'
    ])
    MIN_TRADES_REQUIRED: int = Field(default=10)
    MAX_ALLOWED_LEVERAGE: int = Field(default=20)
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000"
    ])
    
    # MODIFIKASI DISINI: Tambahkan extra="ignore" agar tidak error jika ada variabel baru di .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" 
    )


# Global settings instance
settings = Settings()


# Validation functions
def validate_exchange_config() -> bool:
    """Validate exchange configuration"""
    if settings.EXCHANGE == "weex":
        if not settings.WEEX_API_KEY or not settings.WEEX_API_SECRET:
            # Kita buat jadi warning saja agar bot tetap jalan meski API exchange belum ada
            print("⚠️ WARNING: WEEX API credentials not configured")
    return True


def validate_aws_config() -> bool:
    """Validate AI configuration (Gemini or AWS)"""
    # Jika Gemini API Key ada, maka validasi AI dianggap berhasil
    if settings.GEMINI_API_KEY:
        return True
    # Jika tidak ada Gemini, baru cek AWS
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        print("⚠️ WARNING: AI credentials (Gemini/AWS) not configured")
    return True


def get_exchange_config() -> dict:
    """Get current exchange configuration"""
    if settings.EXCHANGE == "weex":
        return {
            "type": "weex",
            "api_key": settings.WEEX_API_KEY,
            "api_secret": settings.WEEX_API_SECRET,
            "testnet": settings.WEEX_TESTNET,
            "base_url": settings.WEEX_BASE_URL
        }
    return {"type": "none"}


# Export commonly used settings
__all__ = [
    'settings',
    'Settings',
    'validate_exchange_config',
    'validate_aws_config',
    'get_exchange_config'
    ]