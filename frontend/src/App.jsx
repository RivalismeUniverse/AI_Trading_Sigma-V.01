// frontend/src/App.jsx - FIXED VERSION
/**
 * Main App Component - FIXED
 * AI Trading SIGMA Dashboard
 * Fixed: Real balance loading, proper error handling
 */

import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, DollarSign, Target, AlertCircle } from 'lucide-react';
import Header from './components/Header';
import MetricsRow from './components/MetricsRow';
import ChartWidget from './components/ChartWidget';
import OpenPositionsWidget from './components/OpenPositionsWidget';
import RecentTradesWidget from './components/RecentTradesWidget';
import SignalsWidget from './components/SignalsWidget';
import PerformanceWidget from './components/PerformanceWidget';
import CircuitBreakerWidget from './components/CircuitBreakerWidget';
import NotificationPanel from './components/NotificationPanel';
import AIChat from './components/AIChat';
import FloatingAIButton from './components/FloatingAIButton';
import websocketService from './services/websocket';
import * as api from './services/api';
import './App.css';

function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [balance, setBalance] = useState(0); // ✅ FIXED: Start with 0, not 10000
  const [dailyPnL, setDailyPnL] = useState(0);
  const [totalPnL, setTotalPnL] = useState(0);
  const [winRate, setWinRate] = useState(0);
  const [totalTrades, setTotalTrades] = useState(0);
  const [openPositions, setOpenPositions] = useState([]);
  const [recentTrades, setRecentTrades] = useState([]);
  const [currentSignal, setCurrentSignal] = useState(null);
  const [circuitBreakerStatus, setCircuitBreakerStatus] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [showAIChat, setShowAIChat] = useState(false);
  const [loading, setLoading] = useState(true);
  const [connectionError, setConnectionError] = useState(null); // ✅ NEW: Track connection errors

  // Initialize
  useEffect(() => {
    initializeApp();
    setupWebSocket();
    
    return () => {
      websocketService.disconnect();
    };
  }, []);

  const initializeApp = async () => {
    try {
      setLoading(true);
      setConnectionError(null); // ✅ Reset error state
      
      console.log('🔄 Initializing app...');
      
      // ✅ FIXED: Fetch balance FIRST with proper error handling
      let realBalance = 0;
      try {
        const balanceRes = await api.getBalance();
        console.log('📊 Balance API response:', balanceRes);
        
        if (balanceRes.success && balanceRes.balance) {
          realBalance = balanceRes.balance.total || 0;
          console.log(`✅ Real balance loaded: $${realBalance.toFixed(2)}`);
          setBalance(realBalance);
        } else {
          console.warn('⚠️ Balance response invalid:', balanceRes);
          setBalance(0);
        }
      } catch (balanceError) {
        console.error('❌ Failed to fetch balance:', balanceError);
        setConnectionError('Failed to connect to exchange. Check backend connection.');
        setBalance(0);
      }
      
      // Fetch other data in parallel
      const [statusRes, performanceRes, tradesRes, positionsRes, cbRes, notifRes] = await Promise.all([
        api.getTradingStatus().catch(e => ({ success: false, error: e })),
        api.getPerformance().catch(e => ({ success: false, error: e })),
        api.getTrades(10).catch(e => ({ success: false, error: e })),
        api.getOpenPositions().catch(e => ({ success: false, error: e })),
        api.getCircuitBreakerStatus().catch(e => ({ success: false, error: e })),
        api.getNotifications(10).catch(e => ({ success: false, error: e }))
      ]);

      // Update state with proper fallbacks
      if (statusRes.success) {
        setIsRunning(statusRes.status.is_running || false);
        setTotalTrades(statusRes.status.total_trades || 0);
        setTotalPnL(statusRes.status.total_pnl || 0);
        console.log(`ℹ️ Trading status: ${statusRes.status.is_running ? 'RUNNING' : 'STOPPED'}`);
      }

      if (performanceRes.success) {
        setWinRate(performanceRes.metrics.win_rate || 0);
      }

      if (tradesRes.success) {
        setRecentTrades(tradesRes.trades || []);
        console.log(`📈 Loaded ${tradesRes.trades?.length || 0} recent trades`);
      }

      if (positionsRes.success) {
        setOpenPositions(positionsRes.positions || []);
        console.log(`💼 Open positions: ${positionsRes.positions?.length || 0}`);
      }

      if (cbRes.success) {
        setCircuitBreakerStatus(cbRes.status);
      }

      if (notifRes.success) {
        setNotifications(notifRes.notifications || []);
      }

      console.log('✅ App initialized successfully');

    } catch (error) {
      console.error('❌ Failed to initialize app:', error);
      setConnectionError('Failed to initialize dashboard. Please check backend connection.');
      // ✅ Don't set mock balance on error
      setBalance(0);
    } finally {
      setLoading(false);
    }
  };

  const setupWebSocket = () => {
    websocketService.connect();

    // Status updates
    websocketService.on('status_update', (data) => {
      console.log('📡 WebSocket status update:', data);
      setIsRunning(data.is_running);
      setDailyPnL(data.daily_pnl || 0);
      
      // ✅ FIXED: Update balance from WebSocket
      if (data.balance !== undefined && data.balance !== null) {
        console.log(`💰 Balance updated via WebSocket: $${data.balance.toFixed(2)}`);
        setBalance(data.balance);
      }
    });

    // New trade
    websocketService.on('new_trade', (data) => {
      console.log('🆕 New trade:', data);
      setRecentTrades(prev => [data, ...prev].slice(0, 10));
      setTotalTrades(prev => prev + 1);
    });

    // Trade closed
    websocketService.on('trade_closed', (data) => {
      console.log('✅ Trade closed:', data);
      setTotalPnL(prev => prev + (data.pnl || 0));
      setDailyPnL(prev => prev + (data.pnl || 0));
    });

    // Performance update
    websocketService.on('performance_update', (data) => {
      console.log('📊 Performance update:', data);
      if (data.win_rate) setWinRate(data.win_rate);
      if (data.total_pnl) setTotalPnL(data.total_pnl);
      if (data.balance !== undefined) setBalance(data.balance);
    });

    // Signal generated
    websocketService.on('signal_generated', (data) => {
      console.log('🎯 Signal generated:', data);
      setCurrentSignal(data);
    });

    // Circuit breaker alert
    websocketService.on('circuit_breaker_alert', (data) => {
      console.log('⚠️ Circuit breaker alert:', data);
      setCircuitBreakerStatus(prev => ({
        ...prev,
        state: data.state
      }));
      
      // Add notification
      setNotifications(prev => [{
        id: Date.now(),
        timestamp: new Date().toISOString(),
        priority: 'WARNING',
        message: data.message,
        read: false
      }, ...prev]);
    });

    // ✅ NEW: Connection status
    websocketService.on('connection', (data) => {
      if (data.status === 'connected') {
        console.log('✅ WebSocket connected');
        setConnectionError(null);
      } else {
        console.log('⚠️ WebSocket disconnected');
      }
    });
  };

  const handleStartStop = async () => {
    try {
      console.log(`🔄 ${isRunning ? 'Stopping' : 'Starting'} trading...`);
      
      if (isRunning) {
        await api.stopTrading();
        setIsRunning(false);
        console.log('⏹️ Trading stopped');
      } else {
        await api.startTrading();
        setIsRunning(true);
        console.log('▶️ Trading started');
      }
    } catch (error) {
      console.error('❌ Failed to toggle trading:', error);
      alert(`Failed to ${isRunning ? 'stop' : 'start'} trading: ${error.message || error}`);
    }
  };

  const refreshData = async () => {
    console.log('🔄 Refreshing data...');
    await initializeApp();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-16 h-16 text-primary-500 animate-spin mx-auto mb-4" />
          <p className="text-dark-600 text-lg">Loading AI Trading SIGMA...</p>
          <p className="text-dark-500 text-sm mt-2">Connecting to exchange...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-50">
      {/* Header */}
      <Header 
        isRunning={isRunning}
        onStartStop={handleStartStop}
        onRefresh={refreshData}
        balance={balance}
        dailyPnL={dailyPnL}
      />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 space-y-6">
        
        {/* ✅ NEW: Connection Error Alert */}
        {connectionError && (
          <div className="bg-danger-500 bg-opacity-10 border border-danger-500 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-danger-500" />
              <div>
                <h3 className="text-danger-500 font-semibold">Connection Error</h3>
                <p className="text-dark-600 text-sm">{connectionError}</p>
                <button 
                  onClick={refreshData}
                  className="mt-2 text-primary-500 hover:text-primary-600 text-sm font-medium"
                >
                  Retry Connection
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ✅ NEW: Balance Warning */}
        {balance === 0 && !loading && !connectionError && (
          <div className="bg-warning-500 bg-opacity-10 border border-warning-500 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-warning-500" />
              <div>
                <h3 className="text-warning-500 font-semibold">No Balance Detected</h3>
                <p className="text-dark-600 text-sm">
                  Exchange balance is $0. Please check your WEEX testnet account or API configuration.
                </p>
              </div>
            </div>
          </div>
        )}
        
        {/* Metrics Row */}
        <MetricsRow 
          balance={balance}
          dailyPnL={dailyPnL}
          totalPnL={totalPnL}
          winRate={winRate}
          totalTrades={totalTrades}
          openPositions={openPositions.length}
        />

        {/* Circuit Breaker Alert */}
        {circuitBreakerStatus && circuitBreakerStatus.state !== 'CLOSED' && (
          <div className="bg-warning-500 bg-opacity-10 border border-warning-500 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-warning-500" />
              <div>
                <h3 className="text-warning-500 font-semibold">
                  Circuit Breaker: {circuitBreakerStatus.state}
                </h3>
                <p className="text-dark-600 text-sm">
                  System is in {circuitBreakerStatus.state.toLowerCase()} mode. 
                  {circuitBreakerStatus.state === 'HALT' && ' No new positions will be opened.'}
                  {circuitBreakerStatus.state === 'THROTTLE' && ' Trading with reduced risk.'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Chart */}
          <div className="lg:col-span-2 space-y-6">
            <ChartWidget symbol="BTC/USDT" />
            <RecentTradesWidget trades={recentTrades} />
          </div>

          {/* Right Column - Widgets */}
          <div className="space-y-6">
            <OpenPositionsWidget positions={openPositions} />
            <SignalsWidget signal={currentSignal} />
            <CircuitBreakerWidget status={circuitBreakerStatus} />
          </div>
        </div>

        {/* Bottom Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PerformanceWidget />
          <NotificationPanel 
            notifications={notifications}
            onMarkRead={(id) => {
              setNotifications(prev => 
                prev.map(n => n.id === id ? {...n, read: true} : n)
              );
            }}
            onClear={() => setNotifications([])}
          />
        </div>
      </main>

      {/* AI Chat */}
      {showAIChat && (
        <AIChat onClose={() => setShowAIChat(false)} />
      )}

      {/* Floating AI Button */}
      <FloatingAIButton onClick={() => setShowAIChat(true)} />
    </div>
  );
}

export default App;
