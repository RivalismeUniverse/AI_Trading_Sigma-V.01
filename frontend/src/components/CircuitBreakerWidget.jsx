import React from 'react';
import { Shield, AlertCircle, AlertTriangle, X } from 'lucide-react';

function CircuitBreakerWidget({ status }) {
  if (!status) return null;

  const stateColors = {
    'CLOSED': { bg: 'bg-success-500', text: 'text-success-500', icon: Shield },
    'ALERT': { bg: 'bg-warning-500', text: 'text-warning-500', icon: AlertCircle },
    'THROTTLE': { bg: 'bg-warning-600', text: 'text-warning-600', icon: AlertTriangle },
    'HALT': { bg: 'bg-danger-500', text: 'text-danger-500', icon: AlertTriangle },
    'SHUTDOWN': { bg: 'bg-danger-700', text: 'text-danger-700', icon: X }
  };

  const stateInfo = stateColors[status.state] || stateColors['CLOSED'];
  const StateIcon = stateInfo.icon;

  return (
    <div className="bg-dark-100 rounded-lg p-6 border border-dark-200">
      <div className="flex items-center gap-2 mb-4">
        <Shield className="w-5 h-5 text-primary-500" />
        <h3 className="text-lg font-semibold text-dark-900">Circuit Breaker</h3>
      </div>

      <div className="space-y-4">
        {/* State Badge */}
        <div className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg ${stateInfo.bg} bg-opacity-20`}>
          <StateIcon className={`w-5 h-5 ${stateInfo.text}`} />
          <span className={`font-semibold ${stateInfo.text}`}>
            {status.state}
          </span>
        </div>

        {/* Metrics */}
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-dark-600">Consecutive Failures:</span>
            <span className="font-medium text-dark-900">
              {status.consecutive_failures}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-600">Avg API Latency:</span>
            <span className="font-medium text-dark-900">
              {status.metrics?.avg_api_latency_ms?.toFixed(0)}ms
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-600">Recent Issues:</span>
            <span className="font-medium text-dark-900">
              {status.recent_issues || 0}
            </span>
          </div>
        </div>

        {/* Status Message */}
        {status.state !== 'CLOSED' && (
          <div className="bg-dark-50 rounded p-3 text-sm text-dark-900">
            {status.state === 'ALERT' && 'System is monitoring elevated issues. Trading continues normally.'}
            {status.state === 'THROTTLE' && 'Reduced trading mode active. Only high-confidence signals executed.'}
            {status.state === 'HALT' && 'Trading halted. System is closing positions and waiting for recovery.'}
            {status.state === 'SHUTDOWN' && 'System shutdown. Manual intervention required.'}
          </div>
        )}
      </div>
    </div>
  );
}

export default CircuitBreakerWidget;
