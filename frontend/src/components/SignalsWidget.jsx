import React from 'react';
import { Zap, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

function SignalsWidget({ signal }) {
  if (!signal) {
    return (
      <div className="bg-dark-100 rounded-lg p-6 border border-dark-200">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-primary-500" />
          <h3 className="text-lg font-semibold text-dark-900">Current Signal</h3>
        </div>
        <div className="text-center py-8 text-dark-600">
          <AlertCircle className="w-12 h-12 mx-auto mb-2 text-dark-400" />
          <p>Waiting for signal...</p>
        </div>
      </div>
    );
  }

  const isLong = signal.action === 'ENTER_LONG';
  const isShort = signal.action === 'ENTER_SHORT';
  const isWait = signal.action === 'WAIT';

  return (
    <div className="bg-dark-100 rounded-lg p-6 border border-dark-200">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-5 h-5 text-primary-500" />
        <h3 className="text-lg font-semibold text-dark-900">Current Signal</h3>
      </div>

      <div className="space-y-4">
        {/* Action */}
        <div className="text-center py-4 rounded-lg" style={{
          backgroundColor: isLong ? 'rgba(34, 197, 94, 0.1)' : 
                          isShort ? 'rgba(239, 68, 68, 0.1)' : 
                          'rgba(161, 161, 170, 0.1)'
        }}>
          <div className="flex items-center justify-center gap-2 mb-2">
            {isLong && <TrendingUp className="w-6 h-6 text-success-500" />}
            {isShort && <TrendingDown className="w-6 h-6 text-danger-500" />}
            {isWait && <AlertCircle className="w-6 h-6 text-dark-500" />}
            <span className={`text-2xl font-bold ${
              isLong ? 'text-success-500' : 
              isShort ? 'text-danger-500' : 
              'text-dark-500'
            }`}>
              {signal.action}
            </span>
          </div>
          <div className="text-dark-600 text-sm">
            Confidence: <span className="font-medium text-dark-900">
              {(signal.confidence * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Price Info */}
        {!isWait && (
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-dark-600">Current Price:</span>
              <span className="font-medium text-dark-900">
                ${signal.current_price?.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-600">Stop Loss:</span>
              <span className="font-medium text-danger-500">
                ${signal.stop_loss?.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-600">Take Profit:</span>
              <span className="font-medium text-success-500">
                ${signal.take_profit?.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-dark-600">Risk/Reward:</span>
              <span className="font-medium text-primary-500">
                1:{signal.risk_reward?.toFixed(2)}
              </span>
            </div>
          </div>
        )}

        {/* Reasoning */}
        {signal.reasoning && (
          <div className="bg-dark-50 rounded p-3 text-sm">
            <div className="text-dark-600 mb-1">Reasoning:</div>
            <div className="text-dark-900">{signal.reasoning}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SignalsWidget;
