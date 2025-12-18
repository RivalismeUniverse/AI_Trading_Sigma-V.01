/**
 * Main App Component
 * AI Trading SIGMA Dashboard
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
  const [balance, setBalance] = useState(10000);
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
      
      // Fetch initial data
      const [statusRes, balanceRes, performanceRes, tradesRes, positionsRes, cbRes, notifRes] = await Promise.all([
        api.getTradingStatus(),
        api.getBalance(),
        api.getPerformance(),
        api.getTrades(10),
        api.getOpenPositions(),
        api.getCircuitBreakerStatus(),
        api.getNotifications(10)
      ]);

      // Update state
      if (statusRes.success) {
        setIsRunning(statusRes.status.is_running);
        setTotalTrades(statusRes.status.total_trades || 0);
        setTotalPnL(statusRes.status.total_pnl || 0);
      }

      if (balanceRes.success) {
        setBalance(balanceRes.balance.total || 10000);
      }

      if (performanceRes.success) {
        setWinRate(performanceRes.metrics.win_rate || 0);
      }

      if (tradesRes.success) {
        setRecentTrades(tradesRes.trades || []);
      }

      if (positionsRes.success) {
        setOpenPositions(positionsRes.positions || []);
      }

      if (cbRes.success) {
        setCircuitBreakerStatus(cbRes.status);
      }

      if (notifRes.success) {
        setNotifications(notifRes.notifications || []);
      }

    } catch (error) {
      console.error('Failed to initialize app:', error);
    } finally {
      setLoading(false);
    }
  };

  const setupWebSocket = () => {
    websocketService.connect();

    // Status updates
    websocketService.on('status_update', (data) => {
      setIsRunning(data.is_running);
      setDailyPnL(data.daily_pnl || 0);
      if (data.balance) setBalance(data.balance);
    });

    // New trade
    websocketService.on('new_trade', (data) => {
      setRecentTrades(prev => [data, ...prev].slice(0, 10));
      setTotalTrades(prev => prev + 1);
    });

    // Trade closed
    websocketService.on('trade_closed', (data) => {
      setTotalPnL(prev => prev + (data.pnl || 0));
      setDailyPnL(prev => prev + (data.pnl || 0));
    });

    // Performance update
    websocketService.on('performance_update', (data) => {
      if (data.win_rate) setWinRate(data.win_rate);
      if (data.total_pnl) setTotalPnL(data.total_pnl);
    });

    // Signal generated
    websocketService.on('signal_generated', (data) => {
      setCurrentSignal(data);
    });

    // Circuit breaker alert
    websocketService.on('circuit_breaker_alert', (data) => {
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
  };

  const handleStartStop = async () => {
    try {
      if (isRunning) {
        await api.stopTrading();
        setIsRunning(false);
      } else {
        await api.startTrading();
        setIsRunning(true);
      }
    } catch (error) {
      console.error('Failed to toggle trading:', error);
      alert('Failed to ' + (isRunning ? 'stop' : 'start') + ' trading');
    }
  };

  const refreshData = async () => {
    await initializeApp();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-50 flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-16 h-16 text-primary-500 animate-spin mx-auto mb-4" />
          <p className="text-dark-600 text-lg">Loading AI Trading SIGMA...</p>
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
