import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface TrendLineChartProps {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    color: string;
    bgColor?: string;
  }>;
  height?: number;
  options?: any;
}

const TrendLineChart: React.FC<TrendLineChartProps> = ({ labels, datasets, height = 260, options }) => {
  const chartData = {
    labels,
    datasets: datasets.map(ds => ({
      label: ds.label,
      data: ds.data,
      borderColor: ds.color,
      backgroundColor: ds.bgColor || ds.color,
      tension: 0.4,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: ds.color,
      pointBorderWidth: 2,
      fill: false,
      borderWidth: 3,
      spanGaps: true,
    })),
  };
  const defaultOptions = {
    responsive: true,
    plugins: {
      legend: { display: true, position: 'top', labels: { boxWidth: 16, boxHeight: 16, usePointStyle: true } },
      title: { display: false },
    },
    scales: {
      x: {
        title: { display: false },
        grid: { display: false },
        ticks: { color: '#888', font: { size: 13 } },
      },
      y: {
        title: { display: false },
        grid: { display: false },
        ticks: { color: '#888', font: { size: 13 }, stepSize: 1, precision: 0 },
        beginAtZero: true,
      },
    },
    elements: {
      line: { borderJoinStyle: 'round', borderCapStyle: 'round' },
    },
    backgroundColor: 'transparent',
  };
  // Merge custom options with defaults (shallow merge)
  const mergedOptions = { ...defaultOptions, ...options, plugins: { ...defaultOptions.plugins, ...(options?.plugins || {}) }, scales: { ...defaultOptions.scales, ...(options?.scales || {}) } };
  return <Line data={chartData} options={mergedOptions as any} height={height} />;
};

export default TrendLineChart; 