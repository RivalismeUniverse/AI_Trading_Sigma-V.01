// ===== FILE: frontend/src/components/widgets/SignalsWidget.jsx =====
import { TrendingUp } from 'lucide-react';

export const SignalsWidget = ({ indicators = {}, loading = false }) => {
  const getSignalColor = (value, oversold, overbought) => {
    if (value < oversold) return 'text-success-400';
    if (value > overbought) return 'text-danger-400';
    return 'text-gray-400';
  };

  const indicatorsList = [
    { name: 'RSI', value: indicators.rsi || 50, oversold: 30, overbought: 70 },
    { name: 'MACD', value: indicators.macd || 0 },
    { name: 'Stochastic', value: indicators.stochastic || 50, oversold: 20, overbought: 80 },
    { name: 'ADX', value: indicators.adx || 25 },
  ];

  return (
    <Card title="Market Signals" icon={TrendingUp}>
      <div className="space-y-3">
        {loading ? (
          [...Array(4)].map((_, i) => (
            <div key={i} className="h-12 bg-dark-800 animate-pulse rounded"></div>
          ))
        ) : (
          indicatorsList.map((indicator) => (
            <div key={indicator.name} className="flex items-center justify-between p-2 bg-dark-800 rounded">
              <span className="text-sm font-medium text-gray-400">{indicator.name}</span>
              <span className={clsx('text-sm font-semibold', indicator.oversold ? getSignalColor(indicator.value, indicator.oversold, indicator.overbought) : 'text-gray-300')}>
                {indicator.value.toFixed(2)}
              </span>
            </div>
          ))
        )}
      </div>
    </Card>
  );
};
