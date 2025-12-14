// ===== FILE: frontend/src/components/layout/Header.jsx =====
import React from 'react';
import { Play, Square, Bot, DollarSign, TrendingUp, Activity } from 'lucide-react';
import Button from '../common/Button';
import { formatCurrency, formatPercent } from '../../utils/formatters';

const Header = ({ status, metrics, onStartTrading, onStopTrading, onOpenAI }) => {
  const isRunning = status?.is_running;

  return (
    <header className="bg-dark-900 border-b border-dark-700 sticky top-0 z-50">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left: Logo & Title */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Bot className="h-8 w-8 text-primary-500" />
              <div>
                <h1 className="text-xl font-bold text-gradient-primary">WEEX AI Bot</h1>
                <p className="text-xs text-gray-500">Autonomous Trading</p>
              </div>
            </div>
            
            {/* Status Indicator */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-dark-800 rounded-lg">
              <span className={isRunning ? 'status-running' : 'status-stopped'}></span>
              <span className="text-sm font-medium">
                {isRunning ? 'Running' : 'Stopped'}
              </span>
            </div>
          </div>

          {/* Center: Quick Stats */}
          <div className="hidden md:flex items-center gap-6">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500">Balance</p>
                <p className="text-sm font-semibold">{formatCurrency(metrics?.balance || 0)}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500">Daily P&L</p>
                <p className={`text-sm font-semibold ${metrics?.daily_pnl >= 0 ? 'text-success-400' : 'text-danger-400'}`}>
                  {formatCurrency(metrics?.daily_pnl || 0)}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500">Trades Today</p>
                <p className="text-sm font-semibold">{metrics?.daily_trades || 0}</p>
              </div>
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="md"
              icon={Bot}
              onClick={onOpenAI}
            >
              AI Assistant
            </Button>
            
            {!isRunning ? (
              <Button
                variant="success"
                size="md"
                icon={Play}
                onClick={onStartTrading}
              >
                Start Trading
              </Button>
            ) : (
              <Button
                variant="danger"
                size="md"
                icon={Square}
                onClick={onStopTrading}
              >
                Stop Trading
              </Button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
