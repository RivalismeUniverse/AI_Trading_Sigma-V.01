import React, { useState, useEffect } from 'react';
import { BarChart2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import * as api from '../services/api';

function PerformanceWidget() {
  const [performanceData, setPerformanceData] = useState([]);

  useEffect(() => {
    loadPerformanceData();
    const interval = setInterval(loadPerformanceData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadPerformanceData = async () => {
    try {
      const response = await api.getPerformanceHistory(7);
      if (response.success) {
        setPerformanceData(response.history.map(h => ({
          date: new Date(h.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          pnl: h.total_pnl
        })));
      }
    } catch (error) {
      console.error('Failed to load performance data:', error);
    }
  };

  return (
    <div className="bg-dark-100 rounded-lg p-6 border border-dark-200">
      <div className="flex items-center gap-2 mb-4">
        <BarChart2 className="w-5 h-5 text-primary-500" />
        <h3 className="text-lg font-semibold text-dark-900">Performance (7 Days)</h3>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={performanceData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis 
            dataKey="date" 
            stroke="#71717a"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#71717a"
            style={{ fontSize: '12px' }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#18181b', 
              border: '1px solid #27272a',
              borderRadius: '8px'
            }}
          />
          <Line 
            type="monotone" 
            dataKey="pnl" 
            stroke="#22c55e" 
            strokeWidth={2}
            dot={{ fill: '#22c55e', r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PerformanceWidget;
