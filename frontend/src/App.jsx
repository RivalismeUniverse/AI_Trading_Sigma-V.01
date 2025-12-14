// ===== FILE: frontend/src/App.jsx =====
import React, { useState, useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import Header from './components/layout/Header';
import MainLayout from './components/layout/MainLayout';
import FloatingAIButton from './components/layout/FloatingAIButton';
import AIChat from './components/ai/AIChat';
import api, { formatApiError } from './services/api';
import wsService from './services/websocket';
import './styles/globals.css';

function App() {
  // State management
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [positions, setPositions] = useState([]);
  const [trades, setTrades] = useState([]);
  const [indicators, setIndicators] = useState({});
  const [equityCurve, setEquityCurve] = useState([]);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // Initial data fetch
  useEffect(() => {
    const fetchInitialData = async () => {
      setLoading(true);
      try {
        // Fetch all initial data in parallel
        const [statusRes, metricsRes, tradesRes, positionsRes] = await Promise.all([
          api.getTradingStatus(),
          api.getPerformance(),
          api.getTrades(50),
          api.getOpenTrades(),
        ]);

        setStatus(statusRes.status);
        setMetrics(metricsRes.metrics);
        setTrades(tradesRes.trades || []);
        setPositions(positionsRes.trades || []);

        toast.success('Dashboard loaded successfully');
      } catch (error) {
        console.error('Error fetching initial data:', error);
        toast.error(formatApiError(error));
      } finally {
        setLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  // WebSocket connection
  useEffect(() => {
    // Connect to WebSocket
    wsService.connect();

    // Subscribe to events
    const unsubscribeConnected = wsService.on('connected', () => {
      setWsConnected(true);
      toast.success('Real-time updates connected');
    });

    const unsubscribeDisconnected = wsService.on('disconnected', () => {
      setWsConnected(false);
      toast.error('Real-time updates disconnected');
    });

    const unsubscribeStatus = wsService.on('status_update', (data) => {
      setStatus(data.data);
    });

    const unsubscribeNewTrade = wsService.on('new_trade', (data) => {
      setTrades(prev => [data.data, ...prev].slice(0, 50));
      toast.success(`New trade: ${data.data.symbol} ${data.data.side}`);
    });

    const unsubscribePerformance = wsService.on('performance_update', (data) => {
      setMetrics(data.data);
    });

    // Cleanup
    return () => {
      unsubscribeConnected();
      unsubscribeDisconnected();
      unsubscribeStatus();
      unsubscribeNewTrade();
      unsubscribePerformance();
      wsService.disconnect();
    };
  }, []);

  // Periodic data refresh (every 10 seconds)
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [metricsRes, positionsRes] = await Promise.all([
          api.getPerformance(),
          api.getOpenTrades(),
        ]);
        
        setMetrics(metricsRes.metrics);
        setPositions(positionsRes.trades || []);
      } catch (error) {
        console.error('Error refreshing data:', error);
      }
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  // Trading control handlers
  const handleStartTrading = async () => {
    try {
      await api.startTrading();
      toast.success('Trading started successfully');
      
      // Refresh status
      const statusRes = await api.getTradingStatus();
      setStatus(statusRes.status);
    } catch (error) {
      toast.error(formatApiError(error));
    }
  };

  const handleStopTrading = async () => {
    try {
      await api.stopTrading();
      toast.success('Trading stopped successfully');
      
      // Refresh status
      const statusRes = await api.getTradingStatus();
      setStatus(statusRes.status);
    } catch (error) {
      toast.error(formatApiError(error));
    }
  };

  const handleOpenAI = () => {
    setIsChatOpen(true);
  };

  return (
    <div className="min-h-screen bg-dark-950">
      {/* Header */}
      <Header
        status={status}
        metrics={metrics}
        onStartTrading={handleStartTrading}
        onStopTrading={handleStopTrading}
        onOpenAI={handleOpenAI}
      />

      {/* Main Content */}
      <MainLayout
        metrics={metrics}
        chartData={chartData}
        positions={positions}
        trades={trades}
        indicators={indicators}
        equityCurve={equityCurve}
        loading={loading}
      />

      {/* Floating AI Button */}
      <FloatingAIButton
        isOpen={isChatOpen}
        onClick={() => setIsChatOpen(!isChatOpen)}
      />

      {/* AI Chat Panel */}
      <AIChat
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155',
          },
          success: {
            iconTheme: {
              primary: '#22c55e',
              secondary: '#f1f5f9',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#f1f5f9',
            },
          },
        }}
      />

      {/* Connection Status Indicator */}
      {!wsConnected && (
        <div className="fixed bottom-6 left-6 px-4 py-2 bg-yellow-900/50 border border-yellow-700 rounded-lg text-sm text-yellow-400 flex items-center gap-2">
          <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></span>
          Reconnecting to live updates...
        </div>
      )}
    </div>
  );
}

export default App;
