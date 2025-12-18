import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp } from 'lucide-react';

function ChartWidget({ symbol }) {
  const [chartData, setChartData] = useState([]);
  const [timeframe, setTimeframe] = useState('1H');

  useEffect(() => {
    // Generate sample chart data
    const generateData = () => {
      const data = [];
      let price = 50000;
      for (let i = 0; i < 50; i++) {
        price += (Math.random() - 0.5) * 200;
        data.push({
          time: new Date(Date.now() - (50 - i) * 60000).toLocaleTimeString(),
          price: price
        });
      }
      return data;
    };

    setChartData(generateData());
    
    // Update every 5 seconds
    const interval = setInterval(() => {
      setChartData(prev => {
        const newData = [...prev.slice(1)];
        const lastPrice = prev[prev.length - 1].price;
        const newPrice = lastPrice + (Math.random() - 0.5) * 200;
        newData.push({
          time: new Date().toLocaleTimeString(),
          price: newPrice
        });
        return newData;
      });
    }, 5000);

    return () => clearInterval(interval);
  }, [timeframe]);

  return (
    <div className="bg-dark-100 rounded-lg p-6 border border-dark-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary-500" />
          <h3 className="text-lg font-semibold text-dark-900">{symbol}</h3>
          {chartData.length > 0 && (
            <span className="text-2xl font-bold text-dark-900 ml-4">
              ${chartData[chartData.length - 1].price.toFixed(2)}
            </span>
          )}
        </div>
        
        <div className="flex gap-2">
          {['5M', '15M', '1H', '4H', '1D'].map(tf => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                timeframe === tf
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-200 text-dark-600 hover:bg-dark-300'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis 
            dataKey="time" 
            stroke="#71717a"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#71717a"
            style={{ fontSize: '12px' }}
            domain={['auto', 'auto']}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#18181b', 
              border: '1px solid #27272a',
              borderRadius: '8px'
            }}
            labelStyle={{ color: '#a1a1aa' }}
          />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#0ea5e9" 
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ChartWidget;
