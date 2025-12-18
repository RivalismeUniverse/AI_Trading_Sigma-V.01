import React from 'react';
import { Bell, X, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

function NotificationPanel({ notifications, onMarkRead, onClear }) {
  const priorityIcons = {
    'INFO': Info,
    'WARNING': AlertCircle,
    'CRITICAL': AlertTriangle,
    'EMERGENCY': X
  };

  const priorityColors = {
    'INFO': 'text-primary-500',
    'WARNING': 'text-warning-500',
    'CRITICAL': 'text-danger-500',
    'EMERGENCY': 'text-danger-700'
  };

  return (
    <div className="bg-dark-100 rounded-lg p-6 border border-dark-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-primary-500" />
          <h3 className="text-lg font-semibold text-dark-900">Notifications</h3>
          {notifications.length > 0 && (
            <span className="bg-danger-500 text-white px-2 py-0.5 rounded-full text-xs font-medium">
              {notifications.filter(n => !n.read).length}
            </span>
          )}
        </div>
        {notifications.length > 0 && (
          <button
            onClick={onClear}
            className="text-dark-600 hover:text-dark-900 text-sm"
          >
            Clear All
          </button>
        )}
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="text-center py-8 text-dark-600">
            No notifications
          </div>
        ) : (
          notifications.map((notif) => {
            const Icon = priorityIcons[notif.priority] || Info;
            const colorClass = priorityColors[notif.priority] || 'text-primary-500';
            
            return (
              <div
                key={notif.id}
                className={`p-3 rounded-lg border ${
                  notif.read 
                    ? 'bg-dark-50 border-dark-200' 
                    : 'bg-primary-500 bg-opacity-5 border-primary-500'
                }`}
                onClick={() => !notif.read && onMarkRead(notif.id)}
              >
                <div className="flex items-start gap-3">
                  <Icon className={`w-5 h-5 ${colorClass} flex-shrink-0 mt-0.5`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-dark-900 text-sm">{notif.message}</p>
                    <p className="text-dark-600 text-xs mt-1">
                      {formatDistanceToNow(new Date(notif.timestamp), { addSuffix: true })}
                    </p>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default NotificationPanel;
