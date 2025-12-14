// ===== FILE: frontend/src/components/widgets/StatCard.jsx =====
import React from 'react';
import clsx from 'clsx';
import { TrendingUp, TrendingDown } from 'lucide-react';

export const StatCard = ({ title, value, change, changeType = 'percent', icon: Icon, trend, loading = false }) => {
  const isPositive = change > 0;
  const isNegative = change < 0;
  
  return (
    <div className="stat-card">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="stat-label">{title}</p>
          {loading ? (
            <div className="h-8 w-24 bg-dark-700 animate-pulse rounded mt-2"></div>
          ) : (
            <h3 className="stat-value mt-1">{value}</h3>
          )}
          {change !== undefined && !loading && (
            <div className={clsx('stat-change mt-1 flex items-center gap-1', isPositive ? 'stat-change-positive' : isNegative ? 'stat-change-negative' : 'text-gray-400')}>
              {trend && (isPositive ? <TrendingUp className="h-3 w-3" /> : isNegative ? <TrendingDown className="h-3 w-3" /> : null)}
              <span>{isPositive && '+'}{change}{changeType === 'percent' ? '%' : ''}</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className={clsx('p-2 rounded-lg', isPositive ? 'bg-success-900/30' : isNegative ? 'bg-danger-900/30' : 'bg-dark-700')}>
            <Icon className={clsx('h-5 w-5', isPositive ? 'text-success-400' : isNegative ? 'text-danger-400' : 'text-gray-400')} />
          </div>
        )}
      </div>
    </div>
  );
};
