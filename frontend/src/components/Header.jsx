import React from 'react';
import { Activity, Power, RefreshCw, TrendingUp, DollarSign } from 'lucide-react';

function Header({ isRunning, onStartStop, onRefresh, balance, dailyPnL }) {
  return (
    <header className="bg-dark-100 border-b border-dark-200 sticky top-0 z-50 shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          
          {/* Logo */}
          <div className="flex items-center gap-3">
            <Activity className="w-8 h-8 text-primary-500" />
            <div>
              <h1 className="text-xl font-bold text-dark-900">AI Trading SIGMA</h1>
              <p className="text-xs text-dark-500">Autonomous Scalping Bot</p>
            </div>
          </div>

          {/* Balance & P/L */}
          <div className="hidden md:flex items-center gap-6">
            <div className="text-right">
              <div className="flex items-center gap-2 text-dark-600 text-sm">
                <DollarSign className="w-4 h-4" />
                <span>Balance</span>
              </div>
              <div className="text-lg font-bold text-dark-900">
                ${balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="text-right">
              <div className="flex items-center gap-2 text-dark-600 text-sm">
                <TrendingUp className="w-4 h-4" />
                <span>Daily P/L</span>
              </div>
              <div className={`text-lg font-bold ${dailyPnL >= 0 ? 'text-success-500' : 'text-danger-500'}`}>
                {dailyPnL >= 0 ? '+' : ''}{dailyPnL.toFixed(2)} USDT
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            <button
              onClick={onRefresh}
              className="p-2 rounded-lg hover:bg-dark-200 transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-5 h-5 text-dark-600" />
            </button>

            <button
              onClick={onStartStop}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                isRunning
                  ? 'bg-danger-500 hover:bg-danger-600 text-white shadow-glow-danger'
                  : 'bg-success-500 hover:bg-success-600 text-white shadow-glow-success'
              }`}
            >
              <Power className="w-5 h-5" />
              <span>{isRunning ? 'Stop' : 'Start'} Trading</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
