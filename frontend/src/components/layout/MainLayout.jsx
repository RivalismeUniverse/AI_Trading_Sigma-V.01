// ===== FILE: frontend/src/components/layout/MainLayout.jsx =====
import React from 'react';
import { DollarSign, TrendingUp, Activity, Target } from 'lucide-react';
import { StatCard } from '../widgets/StatCard';
import { ChartWidget } from '../widgets/ChartWidget';
import { OpenPositionsWidget } from '../widgets/OpenPositionsWidget';
import { RecentTradesWidget } from '../widgets/RecentTradesWidget';
import { SignalsWidget } from '../widgets/SignalsWidget';
import { PerformanceWidget } from '../widgets/PerformanceWidget';
import { formatCurrency, formatPercent } from '../../utils/formatters';

const MainLayout = ({ metrics, chartData, positions, trades, indicators, equityCurve, loading }) => {
  return (
    <div className="p-6 space-y-6">
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Balance"
          value={formatCurrency(metrics?.balance || 0)}
          change={metrics?.balance_change}
          icon={DollarSign}
          trend
          loading={loading}
        />
        <StatCard
          title="Daily P&L"
          value={formatCurrency(metrics?.daily_pnl || 0)}
          change={metrics?.daily_pnl_percent}
          icon={TrendingUp}
          trend
          loading={loading}
        />
        <StatCard
          title="Win Rate"
          value={formatPercent(metrics?.win_rate || 0, 1, false)}
          change={metrics?.win_rate_change}
          icon={Target}
          trend
          loading={loading}
        />
        <StatCard
          title="Total Trades"
          value={metrics?.total_trades || 0}
          change={metrics?.trades_today}
          changeType="number"
          icon={Activity}
          loading={loading}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart - Large */}
        <div className="lg:col-span-2">
          <ChartWidget data={chartData} loading={loading} />
        </div>

        {/* Signals */}
        <div>
          <SignalsWidget indicators={indicators} loading={loading} />
        </div>
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <OpenPositionsWidget positions={positions} loading={loading} />
        <RecentTradesWidget trades={trades} loading={loading} />
        <PerformanceWidget equityCurve={equityCurve} loading={loading} />
      </div>
    </div>
  );
};

export default MainLayout;
