// ===== FILE: frontend/src/components/widgets/ChartWidget.jsx =====
import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import Card from '../common/Card';

export const ChartWidget = ({ data = [], symbol = 'BTC/USDT', timeframe = '5m' }) => {
  const chartContainerRef = useRef();
  const chart = useRef();
  const series = useRef();

  useEffect(() => {
    if (!chartContainerRef.current) return;

    chart.current = createChart(chartContainerRef.current, {
      layout: { background: { color: '#0f172a' }, textColor: '#94a3b8' },
      grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      timeScale: { timeVisible: true, secondsVisible: false },
    });

    series.current = chart.current.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    const handleResize = () => {
      if (chart.current && chartContainerRef.current) {
        chart.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.current?.remove();
    };
  }, []);

  useEffect(() => {
    if (series.current && data.length > 0) {
      series.current.setData(data);
    }
  }, [data]);

  return (
    <Card title={`${symbol} - ${timeframe}`} className="col-span-2">
      <div ref={chartContainerRef} className="w-full" />
    </Card>
  );
};
