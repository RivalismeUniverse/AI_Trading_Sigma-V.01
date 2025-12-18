
# conftest.py
"""
Pytest configuration and fixtures
Shared test fixtures and setup
"""

import pytest
import asyncio
from typing import Generator
import pandas as pd
import numpy as np

# Set event loop policy for Windows
if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    """Generate sample OHLCV data"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='5min')
    
    close_prices = np.random.uniform(45000, 55000, 200)
    
    data = {
        'timestamp': dates,
        'open': close_prices + np.random.uniform(-100, 100, 200),
        'high': close_prices + np.random.uniform(0, 200, 200),
        'low': close_prices - np.random.uniform(0, 200, 200),
        'close': close_prices,
        'volume': np.random.uniform(100, 1000, 200)
    }
    
    df = pd.DataFrame(data)
    
    # Ensure high is highest and low is lowest
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    return df


@pytest.fixture
def mock_exchange_config():
    """Mock exchange configuration"""
    return {
        'type': 'weex',
        'api_key': 'test_key',
        'api_secret': 'test_secret',
        'testnet': True
    }


@pytest.fixture
def mock_balance():
    """Mock account balance"""
    return {
        'total': 10000.0,
        'free': 9000.0,
        'used': 1000.0,
        'currency': 'USDT',
        'timestamp': '2024-01-01T00:00:00Z'
    }


@pytest.fixture
def mock_ticker():
    """Mock ticker data"""
    return {
        'symbol': 'BTC/USDT:USDT',
        'last': 50000.0,
        'bid': 49990.0,
        'ask': 50010.0,
        'high': 51000.0,
        'low': 49000.0,
        'volume': 1000.0,
        'timestamp': 1704067200000
    }


@pytest.fixture
def mock_order():
    """Mock order response"""
    return {
        'id': 'test_order_123456',
        'symbol': 'BTC/USDT:USDT',
        'type': 'market',
        'side': 'buy',
        'amount': 0.01,
        'price': 50000.0,
        'cost': 500.0,
        'filled': 0.01,
        'remaining': 0.0,
        'status': 'closed',
        'timestamp': 1704067200000
    }


@pytest.fixture
def sample_strategy():
    """Sample trading strategy"""
    return {
        'name': 'Test RSI Strategy',
        'description': 'Simple RSI oversold/overbought strategy',
        'parameters': {
            'symbols': ['BTC/USDT:USDT'],
            'timeframe': '5m',
            'leverage': 10,
            'risk_per_trade': 0.02,
            'indicators': {
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            },
            'entry_conditions': {
                'long': 'RSI < 30',
                'short': 'RSI > 70'
            },
            'exit_conditions': {
                'stop_loss_atr_multiplier': 1.5,
                'take_profit_atr_multiplier': 2.5
            }
        }
    }


@pytest.fixture
def sample_indicators():
    """Sample indicator values"""
    return {
        'rsi': 45.0,
        'macd': 12.5,
        'macd_signal': 10.0,
        'macd_histogram': 2.5,
        'stoch_k': 50.0,
        'stoch_d': 48.0,
        'ema_9': 50000.0,
        'ema_20': 49800.0,
        'ema_50': 49500.0,
        'ema_200': 48000.0,
        'sma_20': 49800.0,
        'bb_upper': 51000.0,
        'bb_middle': 50000.0,
        'bb_lower': 49000.0,
        'bb_width': 0.04,
        'atr': 500.0,
        'adx': 25.0,
        'cci': 0.0,
        'mfi': 50.0,
        'obv': 1000000.0,
        'vwap': 50000.0,
        'mc_probability': 0.65,
        'mc_expected_price': 50500.0,
        'gk_volatility': 0.35,
        'z_score': 0.2,
        'lr_slope': 0.001
    }


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
