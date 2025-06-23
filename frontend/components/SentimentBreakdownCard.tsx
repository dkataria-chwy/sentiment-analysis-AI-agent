import React from 'react';
import { Pie } from 'react-chartjs-2';

interface SentimentStats {
  sentiment_counts: { [sentiment: string]: number };
  sentiment_percentages: { [sentiment: string]: number };
  time_trends?: any;
}

const SENTIMENTS = [
  { key: 'positive', label: 'Positive', color: 'bg-green-400', text: 'text-green-700', icon: '😊' },
  { key: 'neutral', label: 'Neutral', color: 'bg-yellow-300', text: 'text-yellow-700', icon: '😐' },
  { key: 'negative', label: 'Negative', color: 'bg-red-400', text: 'text-red-700', icon: '😞' },
];

export default function SentimentBreakdownCard({ stats }: { stats: SentimentStats }) {
  const data = {
    labels: SENTIMENTS.map(s => s.label),
    datasets: [
      {
        data: SENTIMENTS.map(s => stats.sentiment_counts[s.key] || 0),
        backgroundColor: [
          'rgba(74, 222, 128, 0.7)', // green
          'rgba(253, 224, 71, 0.7)', // yellow
          'rgba(248, 113, 113, 0.7)', // red
        ],
        borderWidth: 2,
      },
    ],
  };

  return (
    <div className="border-2 border-dashed border-blue-200 rounded-xl p-6 bg-white shadow mb-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold mb-1">Sentiment Breakdown</h3>
          <div className="text-gray-500 text-sm mb-2">(for the selected period)</div>
          <div className="flex flex-col gap-2">
            {SENTIMENTS.map(s => (
              <div key={s.key} className="flex items-center gap-2">
                <span className={`text-2xl ${s.text}`}>{s.icon}</span>
                <span className="font-bold text-lg w-16">{stats.sentiment_counts[s.key] || 0}</span>
                <span className={`h-3 w-32 rounded ${s.color} mr-2`}></span>
                <span className="text-gray-700 font-semibold">{stats.sentiment_percentages[s.key] ? stats.sentiment_percentages[s.key].toFixed(2) + '%' : '0%'}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="w-40 h-40 mx-auto md:mx-0">
          <Pie data={data} options={{ plugins: { legend: { display: false } }, cutout: '70%' }} />
        </div>
      </div>
    </div>
  );
} 