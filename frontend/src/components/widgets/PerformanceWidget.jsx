// ===== FILE: frontend/src/components/widgets/PerformanceWidget.jsx =====
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp } from 'lucide-react';

export const PerformanceWidget = ({ equityCurve = [], loading = false }) => {
  const data = equityCurve.map((value, index) => ({
    index,
    equity: value,
  }));

  return (
    <Card title="Equity Curve" icon={TrendingUp}>
      {loading ? (
        <div className="h-48 bg-dark-800 animate-pulse rounded"></div>
      ) : data.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-gray-500">
          <p>No performance data yet</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <XAxis dataKey="index" stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
            <Line type="monotone" dataKey="equity" stroke="#0ea5e9" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
};
