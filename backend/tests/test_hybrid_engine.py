"""
Unit tests for Hybrid Trading Engine.
Tests autonomous trading loop, signal generation, and order execution.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import pandas as pd
import numpy as np
from datetime import datetime

from backend.core.hybrid_engine import HybridTradingEngine
from backend.exchange.weex_client import WEEXClient
from backend.ai.bedrock_client import BedrockClient
from backend.database.db_manager import DatabaseManager
from backend.database.models import TradeStatus, TradeSide

# ===== FIXTURES =====

@pytest.fixture
def mock_exchange():
    """Mock WEEX exchange client"""
    exchange = Mock(spec=WEEXClient)
    exchange.fetch_ohlcv.return_value = [
        [1704067200000, 50000, 50100, 49900, 50050, 1000],
        [1704067500000, 50050, 50150, 49950, 50100, 1100],
        [1704067800000, 50100, 50200, 50000, 50150, 1200],
    ] * 70  # 200+ candles for indicators
    
    exchange.get_balance.return_value = {
        'free': 10000,
        'used': 0,
        'total': 10000
    }
    
    exchange.create_market_order.return_value = {
        'id': 'ORDER_12345',
        'symbol': 'BTC/USDT:USDT',
        'side': 'buy',
        'type': 'market',
        'amount': 0.1,
        'price': 50000,
        'status': 'closed'
    }
    
    return exchange

@pytest.fixture
def mock_ai_client():
    """Mock AI client"""
    ai_client = Mock(spec=BedrockClient)
    ai_client.invoke_model.return_value = {
        'response': 'Market analysis complete',
        'input_tokens': 100,
        'output_tokens': 50
    }
    return ai_client

@pytest.fixture
def mock_db():
    """Mock database manager"""
    db = Mock(spec=DatabaseManager)
    db.create_trade.return_value = Mock(id=1, trade_id='TRADE_001')
    db.get_active_strategy.return_value = None
    db.get_open_trades.return_value = []
    return db

@pytest.fixture
async def engine(mock_exchange, mock_ai_client, mock_db):
    """Create hybrid engine instance"""
    engine = HybridTradingEngine(
        exchange_client=mock_exchange,
        ai_client=mock_ai_client,
        db_manager=mock_db
    )
    return engine

# ===== TESTS =====

class TestHybridEngineInitialization:
    """Test engine initialization"""
    
    def test_engine_initializes_correctly(self, engine):
        """Test that engine initializes with correct default values"""
        assert engine is not None
        assert engine.is_running is False
        assert engine.current_strategy is None
        assert len(engine.active_positions) == 0
    
    def test_components_initialized(self, engine):
        """Test that all components are initialized"""
        assert engine.exchange is not None
        assert engine.ai_client is not None
        assert engine.safety_checker is not None
        assert engine.risk_manager is not None
        assert engine.indicator_calculator is not None

class TestMarketDataFetching:
    """Test market data fetching"""
    
    @pytest.mark.asyncio
    async def test_fetch_market_data_success(self, engine):
        """Test successful market data fetch"""
        ohlcv = await engine.fetch_market_data()
        
        assert ohlcv is not None
        assert isinstance(ohlcv, pd.DataFrame)
        assert len(ohlcv) > 50  # Enough for indicators
        assert 'close' in ohlcv.columns
        assert 'volume' in ohlcv.columns
    
    @pytest.mark.asyncio
    async def test_fetch_market_data_failure(self, engine, mock_exchange):
        """Test market data fetch failure handling"""
        mock_exchange.fetch_ohlcv.return_value = None
        
        ohlcv = await engine.fetch_market_data()
        
        assert ohlcv is None
    
    @pytest.mark.asyncio
    async def test_fetch_market_data_exception(self, engine, mock_exchange):
        """Test exception handling in market data fetch"""
        mock_exchange.fetch_ohlcv.side_effect = Exception("Network error")
        
        ohlcv = await engine.fetch_market_data()
        
        assert ohlcv is None

class TestSignalProcessing:
    """Test signal processing and trade execution"""
    
    @pytest.mark.asyncio
    async def test_process_long_signal(self, engine):
        """Test processing a long entry signal"""
        signal = {
            'action': 'long',
            'confidence': 0.8,
            'entry_price': 50000,
            'stop_loss': 49500,
            'take_profit': 51000,
            'reason': 'RSI oversold'
        }
        
        indicators = {}
        ohlcv = pd.DataFrame({
            'timestamp': [datetime.now()],
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [1000]
        })
        
        # Load a mock strategy
        engine.current_strategy = Mock()
        engine.current_strategy.name = 'Test Strategy'
        engine.current_strategy.leverage = 10
        
        await engine.process_signal(signal, indicators, ohlcv)
        
        # Verify order was created
        engine.exchange.create_market_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_no_signal(self, engine):
        """Test that no signal results in no action"""
        signal = {
            'action': 'none',
            'confidence': 0.0,
            'reason': 'No clear signal'
        }
        
        await engine.process_signal(signal, {}, pd.DataFrame())
        
        # Verify no order was created
        engine.exchange.create_market_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_skip_entry_when_position_exists(self, engine):
        """Test that entry signal is skipped when position exists"""
        # Add existing position
        engine.active_positions['BTC/USDT:USDT'] = {
            'side': 'long',
            'entry_price': 50000
        }
        
        signal = {
            'action': 'long',
            'confidence': 0.8,
            'stop_loss': 49500,
            'take_profit': 51000
        }
        
        ohlcv = pd.DataFrame({'close': [50050]})
        
        await engine.process_signal(signal, {}, ohlcv)
        
        # Verify no new order was created
        engine.exchange.create_market_order.assert_not_called()

class TestPositionManagement:
    """Test position management (stop loss, take profit)"""
    
    @pytest.mark.asyncio
    async def test_stop_loss_hit_long(self, engine):
        """Test stop loss trigger for long position"""
        # Add active position
        engine.active_positions['BTC/USDT:USDT'] = {
            'trade_id': 'TRADE_001',
            'side': 'long',
            'entry_price': 50000,
            'quantity': 0.1,
            'stop_loss': 49500,
            'take_profit': 51000
        }
        
        # Mock current price below stop loss
        ohlcv = pd.DataFrame({
            'close': [49400],  # Below stop loss
            'high': [49500],
            'low': [49300],
            'volume': [1000]
        })
        
        await engine.manage_positions(ohlcv)
        
        # Verify position was closed
        assert 'BTC/USDT:USDT' not in engine.active_positions
    
    @pytest.mark.asyncio
    async def test_take_profit_hit_long(self, engine):
        """Test take profit trigger for long position"""
        engine.active_positions['BTC/USDT:USDT'] = {
            'trade_id': 'TRADE_001',
            'side': 'long',
            'entry_price': 50000,
            'quantity': 0.1,
            'stop_loss': 49500,
            'take_profit': 51000
        }
        
        ohlcv = pd.DataFrame({
            'close': [51100],  # Above take profit
            'high': [51200],
            'low': [51000],
            'volume': [1000]
        })
        
        await engine.manage_positions(ohlcv)
        
        # Verify position was closed
        assert 'BTC/USDT:USDT' not in engine.active_positions

class TestStrategyApplication:
    """Test strategy loading and application"""
    
    def test_apply_strategy(self, engine):
        """Test applying a new strategy"""
        strategy_config = {
            'name': 'Test Strategy',
            'symbol': 'BTC/USDT:USDT',
            'timeframe': '5m',
            'leverage': 10,
            'risk_per_trade': 0.02
        }
        
        engine.apply_strategy(strategy_config)
        
        assert engine.current_strategy is not None
        assert engine.current_strategy.name == 'Test Strategy'
        assert engine.symbol == 'BTC/USDT:USDT'
        assert engine.timeframe == '5m'
    
    def test_load_strategy_from_db(self, engine):
        """Test loading strategy from database model"""
        strategy_model = Mock()
        strategy_model.name = 'DB Strategy'
        strategy_model.symbol = 'ETH/USDT:USDT'
        strategy_model.timeframe = '15m'
        strategy_model.leverage = 5
        strategy_model.config = {'test': 'config'}
        
        engine.load_strategy_from_db(strategy_model)
        
        assert engine.current_strategy is not None
        assert engine.symbol == 'ETH/USDT:USDT'
        assert engine.timeframe == '15m'

class TestEngineControl:
    """Test engine start/stop control"""
    
    @pytest.mark.asyncio
    async def test_start_engine(self, engine):
        """Test starting the engine"""
        # Mock the main loop to avoid infinite loop
        engine._main_loop = AsyncMock()
        
        await engine.start()
        
        # Main loop should have been called
        engine._main_loop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_engine(self, engine):
        """Test stopping the engine"""
        engine.is_running = True
        engine.active_positions['BTC/USDT:USDT'] = {
            'trade_id': 'TRADE_001',
            'side': 'long',
            'entry_price': 50000,
            'quantity': 0.1,
            'stop_loss': 49500,
            'take_profit': 51000
        }
        
        await engine.stop()
        
        assert engine.is_running is False
        # Verify positions were closed
        # (would need to mock execute_exit properly)
    
    def test_get_status(self, engine):
        """Test getting engine status"""
        engine.is_running = True
        engine.current_strategy = Mock(name='Test Strategy')
        engine.daily_trades = 5
        engine.daily_pnl = 123.45
        
        status = engine.get_status()
        
        assert status['is_running'] is True
        assert status['strategy'] == 'Test Strategy'
        assert status['daily_trades'] == 5
        assert status['daily_pnl'] == 123.45

class TestRiskManagement:
    """Test risk management integration"""
    
    @pytest.mark.asyncio
    async def test_daily_loss_limit_prevents_trade(self, engine):
        """Test that daily loss limit prevents new trades"""
        engine.daily_pnl = -600  # -6% loss with 10k balance
        engine.current_strategy = Mock()
        engine.current_strategy.leverage = 10
        
        signal = {
            'action': 'long',
            'confidence': 0.8,
            'stop_loss': 49500,
            'take_profit': 51000
        }
        
        ohlcv = pd.DataFrame({'close': [50000]})
        
        await engine.process_signal(signal, {}, ohlcv)
        
        # Should not create order due to daily loss limit
        engine.exchange.create_market_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_insufficient_balance_prevents_trade(self, engine, mock_exchange):
        """Test that insufficient balance prevents trades"""
        mock_exchange.get_balance.return_value = {
            'free': 5,  # Below minimum
            'total': 5
        }
        
        engine.current_strategy = Mock()
        engine.current_strategy.leverage = 10
        
        signal = {
            'action': 'long',
            'confidence': 0.8,
            'stop_loss': 49500,
            'take_profit': 51000
        }
        
        ohlcv = pd.DataFrame({'close': [50000]})
        
        await engine.process_signal(signal, {}, ohlcv)
        
        # Should not create order due to low balance
        mock_exchange.create_market_order.assert_not_called()

# ===== INTEGRATION TESTS =====

class TestEndToEndTrading:
    """End-to-end trading flow tests"""
    
    @pytest.mark.asyncio
    async def test_complete_trade_cycle(self, engine):
        """Test complete trade from entry to exit"""
        # 1. Apply strategy
        strategy_config = {
            'name': 'E2E Test Strategy',
            'symbol': 'BTC/USDT:USDT',
            'timeframe': '5m',
            'leverage': 10
        }
        engine.apply_strategy(strategy_config)
        
        # 2. Process entry signal
        entry_signal = {
            'action': 'long',
            'confidence': 0.8,
            'stop_loss': 49500,
            'take_profit': 51000,
            'reason': 'RSI oversold'
        }
        
        ohlcv = pd.DataFrame({'close': [50000]})
        await engine.process_signal(entry_signal, {}, ohlcv)
        
        # Verify position opened
        assert len(engine.active_positions) == 1
        
        # 3. Trigger take profit
        ohlcv = pd.DataFrame({'close': [51100]})
        await engine.manage_positions(ohlcv)
        
        # Verify position closed
        assert len(engine.active_positions) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
