import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # AWS Bedrock
    AWS_ACCESS_KEY_ID: str = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY: str = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_REGION: str = os.getenv('AWS_REGION', 'us-east-1')
    BEDROCK_MODEL_ID: str = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
    
    # WEEX Exchange
    WEEX_API_KEY: str = os.getenv('WEEX_API_KEY', '')
    WEEX_API_SECRET: str = os.getenv('WEEX_API_SECRET', '')
    WEEX_TESTNET: bool = os.getenv('WEEX_TESTNET', 'true').lower() == 'true'
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./weex_bot.db')
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Application
    ENV: str = os.getenv('ENV', 'development')
    DEBUG: bool = os.getenv('DEBUG', 'true').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    API_PORT: int = int(os.getenv('API_PORT', '8000'))
    FRONTEND_URL: str = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    # Trading Parameters
    DEFAULT_SYMBOL: str = os.getenv('DEFAULT_SYMBOL', 'BTC/USDT')
    DEFAULT_TIMEFRAME: str = os.getenv('DEFAULT_TIMEFRAME', '5m')
    MAX_RISK_PER_TRADE: float = float(os.getenv('MAX_RISK_PER_TRADE', '0.02'))
    MAX_DAILY_LOSS: float = float(os.getenv('MAX_DAILY_LOSS', '0.05'))
    MAX_POSITIONS: int = int(os.getenv('MAX_POSITIONS', '3'))
    
    # AI Settings
    AI_MODE: str = os.getenv('AI_MODE', 'hybrid')  # hybrid / python_only / ai_only
    AI_STRATEGY_REVIEW_HOURS: int = int(os.getenv('AI_STRATEGY_REVIEW_HOURS', '6'))
    USE_AI_FOR_ENTRIES: bool = os.getenv('USE_AI_FOR_ENTRIES', 'false').lower() == 'true'
    AI_CONFIDENCE_THRESHOLD: float = float(os.getenv('AI_CONFIDENCE_THRESHOLD', '0.7'))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = []
        
        if cls.AI_MODE in ['hybrid', 'ai_only']:
            if not cls.AWS_ACCESS_KEY_ID:
                required.append('AWS_ACCESS_KEY_ID')
            if not cls.AWS_SECRET_ACCESS_KEY:
                required.append('AWS_SECRET_ACCESS_KEY')
        
        if not cls.WEEX_TESTNET:
            if not cls.WEEX_API_KEY:
                required.append('WEEX_API_KEY')
            if not cls.WEEX_API_SECRET:
                required.append('WEEX_API_SECRET')
        
        if required:
            raise ValueError(f"Missing required environment variables: {', '.join(required)}")
        
        return True

config = Config()
