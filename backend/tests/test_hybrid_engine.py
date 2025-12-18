"""
Test Suite for Hybrid Trading Engine
Tests core functionality of the trading system
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd
import numpy as np

from core.hybrid_engine import HybridTradingEngine
from core.signal_generator import SignalGenerator
from core.risk_manager import RiskManager
from exchange.safety_checker import SafetyChecker
from strategies.technical_indicators import TechnicalIndicators


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=200, freq='5min')
    np.random.seed(42)
    
    data = {
        'timestamp': dates,
        'open': np.random.uniform(40000, 50000, 200),
        'high': np.random.uniform(40000, 50000, 200),
        'low': np.random.uniform(40000, 50000, 200),
        'close': np.random.uniform(40000, 50000, 200),
        'volume': np.random.uniform(100, 1000, 200)
    }
    
    return pd.DataFrame(data)


class TestTechnicalIndicators:
    """Test technical indicator calculations"""
    
    def test_rsi_calculation(self, sample_ohlcv_data):
        """Test RSI calculation"""
        indicators = TechnicalIndicators()
        rsi = indicators.rsi(sample_ohlcv_data['close'])
        
        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100
    
    def test_macd_calculation(self, sample_ohlcv_data):
        """Test MACD calculation"""
        indicators = TechnicalIndicators()
        macd, signal, histogram = indicators.macd(sample_ohlcv_data['close'])
        
        assert isinstance(macd, float)
        assert isinstance(signal, float)
        assert isinstance(histogram, float)
    
    def test_bollinger_bands(self, sample_ohlcv_data):
        """Test Bollinger Bands calculation"""
        indicators = TechnicalIndicators()
        upper, middle, lower = indicators.bollinger_bands(sample_ohlcv_data['close'])
        
        assert upper > middle > lower
        assert isinstance(upper, float)
    
    def test_atr_calculation(self, sample_ohlcv_data):
        """Test ATR calculation"""
        indicators = TechnicalIndicators()
        atr = indicators.atr(
            sample_ohlcv_data['high'],
            sample_ohlcv_data['low'],
            sample_ohlcv_data['close']
        )
        
        assert isinstance(atr, float)
        assert atr >= 0
    
    def test_monte_carlo_simulation(self, sample_ohlcv_data):
        """Test Monte Carlo simulation"""
        indicators = TechnicalIndicators()
        probability, expected_price = indicators.monte_carlo_simulation(
            sample_ohlcv_data['close']
        )
        
        assert 0 <= probability <= 1
        assert expected_price > 0
    
    def test_all_indicators(self, sample_ohlcv_data):
        """Test calculation of all indicators"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_all(sample_ohlcv_data)
        
        assert isinstance(result, dict)
        assert 'rsi' in result
        assert 'macd' in result
        assert 'mc_probability' in result
        assert len(result) >= 16  # Should have all 16 indicators


class TestSignalGenerator:
    """Test signal generation"""
    
    def test_signal_generation(self, sample_ohlcv_data):
        """Test basic signal generation"""
        generator = SignalGenerator()
        signal = generator.generate_signal(sample_ohlcv_data, 'BTC/USDT:USDT')
        
        assert 'action' in signal
        assert 'confidence' in signal
        assert 'reasoning' in signal
        assert 0 <= signal['confidence'] <= 1
    
    def test_long_score_calculation(self, sample_ohlcv_data):
        """Test long score calculation"""
        generator = SignalGenerator()
        indicators = TechnicalIndicators().calculate_all(sample_ohlcv_data)
        
        long_score = generator._calculate_long_score(indicators)
        
        assert isinstance(long_score, float)
        assert 0 <= long_score <= 1
    
    def test_short_score_calculation(self, sample_ohlcv_data):
        """Test short score calculation"""
        generator = SignalGenerator()
        indicators = TechnicalIndicators().calculate_all(sample_ohlcv_data)
        
        short_score = generator._calculate_short_score(indicators)
        
        assert isinstance(short_score, float)
        assert 0 <= short_score <= 1


class TestRiskManager:
    """Test risk management"""
    
    def test_position_size_calculation(self):
        """Test position size calculation"""
        risk_manager = RiskManager()
        
        size = risk_manager.calculate_position_size(
            balance=10000,
            risk_pct=0.02,
            entry_price=50000,
            stop_loss_price=49000,
            leverage=10,
            confidence=0.7
        )
        
        assert size > 0
        assert isinstance(size, float)
    
    def test_stop_loss_calculation(self):
        """Test stop loss calculation"""
        risk_manager = RiskManager()
        
        stop_loss = risk_manager.calculate_stop_loss(
            entry_price=50000,
            atr=500,
            direction='long'
        )
        
        assert stop_loss < 50000
        assert isinstance(stop_loss, float)
    
    def test_take_profit_calculation(self):
        """Test take profit calculation"""
        risk_manager = RiskManager()
        
        take_profit = risk_manager.calculate_take_profit(
            entry_price=50000,
            stop_loss_price=49000,
            direction='long'
        )
        
        assert take_profit > 50000
        assert isinstance(take_profit, float)
    
    def test_risk_validation(self):
        """Test risk validation"""
        risk_manager = RiskManager()
        
        is_valid, error = risk_manager.validate_risk(
            position_size=0.1,
            entry_price=50000,
            balance=10000,
            open_positions=0
        )
        
        assert isinstance(is_valid, bool)


class TestSafetyChecker:
    """Test safety and compliance checks"""
    
    def test_symbol_validation(self):
        """Test symbol validation"""
        checker = SafetyChecker()
        
        # Valid symbol
        is_valid, error = checker._check_symbol('BTC/USDT:USDT')
        assert is_valid is True
        
        # Invalid symbol
        is_valid, error = checker._check_symbol('INVALID/SYMBOL')
        assert is_valid is False
        assert error is not None
    
    def test_leverage_validation(self):
        """Test leverage validation"""
        checker = SafetyChecker()
        
        # Valid leverage
        is_valid, error = checker._check_leverage(10)
        assert is_valid is True
        
        # Invalid leverage (too high)
        is_valid, error = checker._check_leverage(50)
        assert is_valid is False
        assert error is not None
    
    def test_trade_validation(self):
        """Test complete trade validation"""
        checker = SafetyChecker()
        
        is_valid, error = checker.validate_trade(
            symbol='BTC/USDT:USDT',
            side='buy',
            amount=0.01,
            leverage=10,
            price=50000,
            account_balance=10000
        )
        
        assert isinstance(is_valid, bool)
    
    def test_compliance_report(self):
        """Test compliance report generation"""
        checker = SafetyChecker()
        report = checker.get_compliance_report()
        
        assert 'allowed_symbols' in report
        assert 'max_leverage' in report
        assert 'compliance_rate' in report


@pytest.mark.asyncio
class TestHybridTradingEngine:
    """Test hybrid trading engine"""
    
    async def test_engine_initialization(self):
        """Test engine initialization"""
        with patch('core.hybrid_engine.get_exchange_config') as mock_config:
            mock_config.return_value = {
                'type': 'weex',
                'api_key': 'test',
                'api_secret': 'test',
                'testnet': True
            }
            
            engine = HybridTradingEngine()
            assert engine.is_running is False
            assert engine.trade_count == 0
    
    async def test_status_retrieval(self):
        """Test status retrieval"""
        engine = HybridTradingEngine()
        
        # Mock exchange client
        engine.exchange_client = AsyncMock()
        engine.exchange_client.fetch_balance.return_value = {'total': 10000}
        
        status = await engine.get_status()
        
        assert 'is_running' in status
        assert 'balance' in status
        assert 'total_trades' in status


# Helper functions for tests
def create_mock_order():
    """Create mock order response"""
    return {
        'id': 'test_order_123',
        'symbol': 'BTC/USDT:USDT',
        'side': 'buy',
        'amount': 0.01,
        'price': 50000,
        'status': 'filled'
    }


def create_mock_balance():
    """Create mock balance response"""
    return {
        'total': 10000,
        'free': 9000,
        'used': 1000,
        'currency': 'USDT'
    }


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
