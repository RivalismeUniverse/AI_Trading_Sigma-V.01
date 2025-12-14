// ===== FILE: frontend/src/components/widgets/OpenPositionsWidget.jsx =====
import { Activity } from 'lucide-react';
import { formatCurrency, formatPercent, formatSymbol } from '../../utils/formatters';

export const OpenPositionsWidget = ({ positions = [], loading = false }) => {
  return (
    <Card title="Open Positions" icon={Activity}>
      <div className="space-y-3">
        {loading ? (
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-dark-800 animate-pulse rounded"></div>
            ))}
          </div>
        ) : positions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Activity className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>No open positions</p>
          </div>
        ) : (
          positions.map((position, index) => {
            const pnlPercent = ((position.current_price - position.entry_price) / position.entry_price) * 100 * (position.side === 'long' ? 1 : -1);
            const isProfit = pnlPercent > 0;

            return (
              <div key={index} className="p-3 bg-dark-800 rounded-lg border border-dark-700 hover:border-primary-700 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{formatSymbol(position.symbol)}</span>
                  <span className={clsx('badge', position.side === 'long' ? 'badge-success' : 'badge-danger')}>
                    {position.side.toUpperCase()}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-gray-500">Entry</p>
                    <p className="font-medium">{formatCurrency(position.entry_price)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">Current</p>
                    <p className="font-medium">{formatCurrency(position.current_price)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">P&L</p>
                    <p className={clsx('font-semibold', isProfit ? 'text-success-400' : 'text-danger-400')}>
                      {formatPercent(pnlPercent)}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">Size</p>
                    <p className="font-medium">{position.quantity} {position.leverage}x</p>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
};
