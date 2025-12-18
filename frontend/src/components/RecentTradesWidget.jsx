import React from 'react';
import { Activity, TrendingUp, TrendingDown, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

function RecentTradesWidget({ trades }) {
  return (
    <div className="bg-dark-100 rounded-lg p-6 border border-dark-200">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-primary-500" />
        <h3 className="text-lg font-semibold text-dark-900">Recent Trades</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-dark-600 text-sm border-b border-dark-200">
              <th className="pb-2">Symbol</th>
              <th className="pb-2">Side</th>
              <th className="pb-2">Entry</th>
              <th className="pb-2">Exit</th>
              <th className="pb-2">P/L</th>
              <th className="pb-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {trades.length === 0 ? (
              <tr>
                <td colSpan="6" className="py-8 text-center text-dark-600">
                  No trades yet
                </td>
              </tr>
            ) : (
              trades.map((trade, index) => (
                <tr key={index} className="border-b border-dark-200 hover:bg-dark-50">
                  <td className="py-3 font-medium text-dark-900">
                    {trade.symbol}
                  </td>
                  <td className="py-3">
                    <div className="flex items-center gap-1">
                      {trade.action === 'ENTER_LONG' ? (
                        <>
                          <TrendingUp className="w-4 h-4 text-success-500" />
                          <span className="text-success-500 text-sm font-medium">LONG</span>
                        </>
                      ) : (
                        <>
                          <TrendingDown className="w-4 h-4 text-danger-500" />
                          <span className="text-danger-500 text-sm font-medium">SHORT</span>
                        </>
                      )}
                    </div>
                  </td>
                  <td className="py-3 text-dark-900">
                    ${trade.entry_price?.toFixed(2)}
                  </td>
                  <td className="py-3 text-dark-900">
                    {trade.exit_price ? `$${trade.exit_price.toFixed(2)}` : '-'}
                  </td>
                  <td className="py-3">
                    <span className={`font-medium ${
                      (trade.pnl || 0) >= 0 ? 'text-success-500' : 'text-danger-500'
                    }`}>
                      {trade.pnl ? `${trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}` : '-'}
                    </span>
                  </td>
                  <td className="py-3 text-dark-600 text-sm">
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {trade.entry_time ? 
                        formatDistanceToNow(new Date(trade.entry_time), { addSuffix: true }) 
                        : '-'}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default RecentTradesWidget;
