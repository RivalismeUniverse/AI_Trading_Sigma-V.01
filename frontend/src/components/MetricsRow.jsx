import React from 'react';
import { DollarSign, TrendingUp, Target, Activity, Users, Award } from 'lucide-react';

function MetricsRow({ balance, dailyPnL, totalPnL, winRate, totalTrades, openPositions }) {
  const metrics = [
    {
      icon: DollarSign,
      label: 'Balance',
      value: `$${balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      color: 'text-primary-500',
      bgColor: 'bg-primary-500 bg-opacity-10'
    },
    {
      icon: TrendingUp,
      label: 'Daily P/L',
      value: `${dailyPnL >= 0 ? '+' : ''}${dailyPnL.toFixed(2)} USDT`,
      color: dailyPnL >= 0 ? 'text-success-500' : 'text-danger-500',
      bgColor: dailyPnL >= 0 ? 'bg-success-500 bg-opacity-10' : 'bg-danger-500 bg-opacity-10'
    },
    {
      icon: Target,
      label: 'Total P/L',
      value: `${totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)} USDT`,
      color: totalPnL >= 0 ? 'text-success-500' : 'text-danger-500',
      bgColor: totalPnL >= 0 ? 'bg-success-500 bg-opacity-10' : 'bg-danger-500 bg-opacity-10'
    },
    {
      icon: Award,
      label: 'Win Rate',
      value: `${winRate.toFixed(1)}%`,
      color: winRate >= 60 ? 'text-success-500' : 'text-warning-500',
      bgColor: winRate >= 60 ? 'bg-success-500 bg-opacity-10' : 'bg-warning-500 bg-opacity-10'
    },
    {
      icon: Activity,
      label: 'Total Trades',
      value: totalTrades,
      color: 'text-primary-500',
      bgColor: 'bg-primary-500 bg-opacity-10'
    },
    {
      icon: Users,
      label: 'Open Positions',
      value: openPositions,
      color: 'text-primary-500',
      bgColor: 'bg-primary-500 bg-opacity-10'
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {metrics.map((metric, index) => (
        <div 
          key={index}
          className="bg-dark-100 rounded-lg p-4 border border-dark-200 hover:border-dark-300 transition-all"
        >
          <div className={`inline-flex p-2 rounded-lg ${metric.bgColor} mb-2`}>
            <metric.icon className={`w-5 h-5 ${metric.color}`} />
          </div>
          <div className="text-dark-600 text-sm mb-1">{metric.label}</div>
          <div className={`text-xl font-bold ${metric.color}`}>
            {metric.value}
          </div>
        </div>
      ))}
    </div>
  );
}

export default MetricsRow;
