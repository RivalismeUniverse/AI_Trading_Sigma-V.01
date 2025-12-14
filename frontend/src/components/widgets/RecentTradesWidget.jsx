// ===== FILE: frontend/src/components/widgets/RecentTradesWidget.jsx =====
import { History } from 'lucide-react';
import { formatCurrency, formatRelativeTime, formatSymbol, formatPercent } from '../../utils/formatters';

export const RecentTradesWidget = ({ trades = [], loading = false }) => {
  return (
    <Card title="Recent Trades" icon={History}>
      <div className="space-y-2">
        {loading ? (
          [...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-dark-800 animate-pulse rounded"></div>
          ))
        ) : trades.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <History className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>No trades yet</p>
          </div>
        ) : (
          trades.slice(0, 5).map((trade) => {
            const isProfit = trade.pnl > 0;
            return (
              <div key={trade.id} className="p-2 bg-dark-800 rounded hover:bg-dark-700 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={clsx('badge', trade.side === 'long' ? 'badge-success' : 'badge-danger')}>
                      {trade.side === 'long' ? '📈' : '📉'}
                    </span>
                    <div>
                      <p className="font-medium text-sm">{formatSymbol(trade.symbol)}</p>
                      <p className="text-xs text-gray-500">{formatRelativeTime(trade.closed_at)}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={clsx('font-semibold text-sm', isProfit ? 'text-success-400' : 'text-danger-400')}>
                      {isProfit && '+'}{formatCurrency(trade.pnl)}
                    </p>
                    <p className="text-xs text-gray-500">{formatPercent(trade.pnl_percent)}</p>
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
