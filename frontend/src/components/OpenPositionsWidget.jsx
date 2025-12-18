import React from 'react';
import { Users, TrendingUp, TrendingDown } from 'lucide-react';

function OpenPositionsWidget({ positions }) {
  return (
    <div className="bg-dark-100 rounded-lg p-6 border border-dark-200">
      <div className="flex items-center gap-2 mb-4">
        <Users className="w-5 h-5 text-primary-500" />
        <h3 className="text-lg font-semibold text-dark-900">Open Positions</h3>
        <span className="ml-auto bg-primary-500 bg-opacity-20 text-primary-500 px-2 py-1 rounded text-sm font-medium">
          {positions.length}
        </span>
      </div>

      <div className="space-y-3">
        {positions.length === 0 ? (
          <div className="text-center py-8 text-dark-600">
            No open positions
          </div>
        ) : (
          positions.map((position, index) => (
            <div 
              key={index}
              className="bg-dark-50 rounded-lg p-4 border border-dark-200"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {position.side === 'ENTER_LONG' ? (
                    <TrendingUp className="w-4 h-4 text-success-500" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-danger-500" />
                  )}
                  <span className="font-semibold text-dark-900">
                    {position.symbol}
                  </span>
                </div>
                <span className={`text-sm font-medium ${
                  (position.current_pnl || 0) >= 0 ? 'text-success-500' : 'text-danger-500'
                }`}>
                  {(position.current_pnl || 0) >= 0 ? '+' : ''}{(position.current_pnl || 0).toFixed(2)} USDT
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-dark-600">Entry:</span>
                  <span className="ml-2 text-dark-900 font-medium">
                    ${position.entry_price?.toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-dark-600">Size:</span>
                  <span className="ml-2 text-dark-900 font-medium">
                    {position.position_size?.toFixed(4)}
                  </span>
                </div>
                <div>
                  <span className="text-dark-600">SL:</span>
                  <span className="ml-2 text-dark-900 font-medium">
                    ${position.stop_loss?.toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-dark-600">TP:</span>
                  <span className="ml-2 text-dark-900 font-medium">
                    ${position.take_profit?.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default OpenPositionsWidget;
