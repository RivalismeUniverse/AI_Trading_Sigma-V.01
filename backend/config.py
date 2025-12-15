"""
Configuration management for AI Trading SIGMA
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    app_name: str = "AI Trading SIGMA"
    debug: bool = True
    log_level: str = "INFO"
    
    # AWS Bedrock
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    # Exchanges
    binance_testnet_api_key: Optional[str] = None
    binance_testnet_api_secret: Optional[str] = None
    binance_testnet: bool = True
    
    weex_api_key: Optional[str] = None
    weex_api_secret: Optional[str] = None
    weex_testnet: bool = True
    
    # Trading
    default_symbol: str = "BTC/USDT"
    allowed_symbols: List[str] = Field(
        default=[
            "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
            "ADA/USDT", "XRP/USDT", "DOGE/USDT", "LTC/USDT"
        ]
    )
    default_leverage: int = 10
    max_leverage: int = 20
    max_risk_per_trade: float = 0.02  # 2%
    max_daily_loss: float = 0.05  # 5%
    initial_balance: float = 10000
    
    # Risk Management
    stop_loss_atr_multiplier: float = 1.5
    take_profit_atr_multiplier: float = 2.5
    trailing_stop_activation: float = 0.5  # 0.5% profit
    trailing_stop_distance: float = 0.3  # 0.3% below peak
    
    # Indicators
    rsi_period: int = 14
    rsi_oversold: int = 30
    rsi_overbought: int = 70
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bollinger_period: int = 20
    bollinger_std: float = 2.0
    ema_short: int = 9
    ema_medium: int = 20
    ema_long: int = 50
    
    # Monte Carlo
    monte_carlo_simulations: int = 1000
    monte_carlo_periods: int = 20
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./trading.db"
    
    # Frontend
    frontend_url: str = "http://localhost:3000"
    
    # Paths
    log_dir: str = "./logs"
    data_dir: str = "./data"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def exchange_to_use(self) -> str:
        """Determine which exchange to use based on configuration"""
        if self.binance_testnet_api_key and self.binance_testnet:
            return "binance_testnet"
        elif self.weex_api_key:
            return "weex"
        else:
            return "binance_testnet"  # Default for testing
    
    @property
    def is_testnet(self) -> bool:
        """Check if we're using testnet"""
        if self.exchange_to_use == "binance_testnet":
            return True
        elif self.exchange_to_use == "weex":
            return self.weex_testnet
        return True
    
    def get_exchange_config(self) -> dict:
        """Get exchange configuration"""
        if self.exchange_to_use == "binance_testnet":
            return {
                "apiKey": self.binance_testnet_api_key,
                "secret": self.binance_testnet_api_secret,
                "enableRateLimit": True,
                "options": {"defaultType": "future"},
                "urls": {
                    "api": {
                        "public": "https://testnet.binancefuture.com/fapi/v1",
                        "private": "https://testnet.binancefuture.com/fapi/v1",
                    }
                }
            }
        else:  # WEEX
            return {
                "apiKey": self.weex_api_key,
                "secret": self.weex_secret,
                "enableRateLimit": True,
                "options": {"defaultType": "swap"}
            }


# Global settings instance
settings = Settings()
