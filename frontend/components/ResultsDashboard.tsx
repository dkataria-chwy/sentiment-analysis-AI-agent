import React, { useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import KeywordChipList from './KeywordChipList';
import { useRouter } from 'next/router';
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

interface Props {
  data: any;
  summaryLoading?: boolean;
  summaryError?: string;
}

// Helper: Generate a verdict string based on sentiment distribution
function getSentimentVerdict(counts: any, percentages: any): string {
  const pos = percentages.positive || 0;
  const neu = percentages.neutral || 0;
  const neg = percentages.negative || 0;
  // Find the majority sentiment
  const max = Math.max(pos, neu, neg);
  let majority: 'positive' | 'neutral' | 'negative' = 'positive';
  if (max === neg) majority = 'negative';
  else if (max === neu) majority = 'neutral';
  // Now assign verdict based on which is majority
  if (majority === 'positive') {
    if (pos >= 80) return 'Overwhelmingly Positive';
    if (pos >= 60) return 'Mostly Positive';
    return 'Mixed';
  }
  if (majority === 'negative') {
    if (neg >= 80) return 'Overwhelmingly Negative';
    if (neg >= 60) return 'Mostly Negative';
    return 'Mixed';
  }
  // Neutral majority
  return 'Mixed or Neutral';
}

export default function ResultsDashboard({ data, summaryLoading, summaryError }: Props) {
  const router = useRouter();

  // Dynamically import chartjs-plugin-zoom and hammerjs only on the client
  useEffect(() => {
    if (typeof window !== 'undefined') {
      import('chartjs-plugin-zoom').then((zoomPlugin) => {
        if (zoomPlugin && zoomPlugin.default) {
          ChartJS.register(zoomPlugin.default);
        }
      });
      import('hammerjs');
    }
  }, []);

  // Preprocess summary: make theme lines into subheaders
  const formattedSummary = data?.summary
    // Remove the main title if present
    ?.replace(/^.*Executive Summary:.*\n?/im, '')
    
    // Make theme lines (not already headers) into ### subheaders
    .replace(/^(?!#)([A-Z][A-Za-z &\-\/]+):?\s*$/gm, '### $1')
    // Remove extra blank lines
    // .replace(/\n{3,}/g, '\n\n');

  return (
    <div className="relative max-w-7xl mx-auto mt-12 mb-24 p-8 bg-white/80 backdrop-blur-md rounded-2xl shadow-2xl border-2 border-blue-300/60 flex flex-col overflow-hidden">
      {/* Top action buttons */}
      <div className="flex gap-4 mb-8 justify-end">
        <button
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 shadow"
          onClick={async () => {
            const card = document.getElementById('results-dashboard-card');
            if (card) {
              // Save original styles
              const originalOverflow = card.style.overflow;
              const originalWidth = card.style.width;
              card.style.overflow = 'visible';
              card.style.width = 'auto';
              const canvas = await html2canvas(card, { background: '#fff', useCORS: true });
              const imgData = canvas.toDataURL('image/png');
              const printWindow = window.open('', '', 'width=900,height=700');
              printWindow.document.write('<html><head><title>Export PDF</title>');
              Array.from(document.head.children).forEach(el => printWindow.document.head.appendChild(el.cloneNode(true)));
              printWindow.document.write('</head><body style="margin:0;padding:0;text-align:center;background:#f8fafc;">');
              printWindow.document.write(`<img src="${imgData}" style="max-width:100%;height:auto;"/>`);
              printWindow.document.write('</body></html>');
              printWindow.document.close();
              printWindow.focus();
              setTimeout(() => printWindow.print(), 500);
              // Restore original styles
              card.style.overflow = originalOverflow;
              card.style.width = originalWidth;
            }
          }}
        >Export as PDF</button>
        <button
          className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 shadow"
          onClick={() => {
            const json = JSON.stringify({ summary: data?.summary, stats: data?.stats }, null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'sentiment_analysis_result.json';
            a.click();
            URL.revokeObjectURL(url);
          }}
        >Export as JSON</button>
        <button
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 shadow"
          onClick={() => router.push('/')}
        >Analyze another SKU</button>
      </div>
      {/* Left accent bar */}
      <div className="absolute left-0 top-0 h-full w-0 bg-gradient-to-b from-blue-500 via-purple-400 to-pink-400 rounded-l-2xl" />
      {/* Card content */}
      <div className="pl-6" id="results-dashboard-card">
        {/* Executive Summary Header at the top, centered */}
        <h2 className="text-3xl font-bold mb-8 text-center">Executive Summary</h2>
        {/* Community Sentiment Bar */}
        {data?.stats?.sentiment_counts && data?.stats?.sentiment_percentages && (() => {
          // Determine order: majority sentiment first
          const counts = data.stats.sentiment_counts;
          const percentages = data.stats.sentiment_percentages;
          const sentiments = [
            { key: 'negative', label: 'Negative', color: 'bg-[#FFA07A]', icon: '😡', text: 'text-[#D97706]', percent: percentages.negative || 0, count: counts.negative || 0 },
            { key: 'neutral', label: 'Neutral', color: 'bg-yellow-300', icon: '😐', text: 'text-yellow-600', percent: percentages.neutral || 0, count: counts.neutral || 0 },
            { key: 'positive', label: 'Positive', color: 'bg-blue-400', icon: '😊', text: 'text-blue-700', percent: percentages.positive || 0, count: counts.positive || 0 },
          ];
          sentiments.sort((a, b) => b.count - a.count);
          return (
            <div className="mb-8">
              <div className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-1">Community Sentiment</div>
              <div className="text-2xl md:text-3xl font-extrabold mb-2">
                {getSentimentVerdict(counts, percentages)}
              </div>
              {/* Horizontal bar */}
              <div className="flex h-4 w-full overflow-hidden mb-4 gap-x-1" style={{maxWidth: '100%'}}>
                {sentiments.map((s, i) => (
                  <div key={s.key} className={s.color + ' rounded-full'} style={{width: `${s.percent}%`}} />
                ))}
              </div>
              {/* Sentiment counts and percentages */}
              <div className="flex justify-between max-w-md">
                {sentiments.map((s) => (
                  <div key={s.key} className="flex flex-col items-center flex-1">
                    <span className={s.text + ' text-lg'}>{s.icon}</span>
                    <span className="font-semibold text-gray-700">{s.label}</span>
                    <span className={"font-bold " + s.text}>{s.count}</span>
                    <span className="text-xs text-gray-500">{s.percent.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })()}
        {/* Executive Summary */}
        <div className="mb-6 text-gray-700">
          {summaryLoading ? (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="flex gap-2 text-4xl animate-pulse">
                <span role="img" aria-label="AI">✨</span>
              </div>
              <div className="mt-4 text-blue-700 font-semibold text-lg">Generating executive summary...</div>
            </div>
          ) : summaryError ? (
            summaryError
          ) : (
            <ReactMarkdown
              components={{
                h3: ({node, ...props}) => (
                  <h3
                    className="text-xl font-bold text-gray-900 mb-2 mt-4 flex items-center gap-2"
                    {...props}
                  >
                    {props.children} <span role="img" aria-label="AI">✨</span>
                  </h3>
                ),
                h4: ({node, ...props}) => (
                  <h4
                    className="text-lg font-semibold mt-4 mb-3"
                    {...props}
                  />
                ),
                strong: ({node, ...props}) => {
                  if (typeof props.children[0] === 'string') {
                    if (props.children[0].startsWith('Positive:')) {
                      return <strong className="text-blue-700 font-bold">{props.children}</strong>;
                    }
                    if (props.children[0].startsWith('Negative:')) {
                      return <strong className="text-[#D97706] font-bold">{props.children}</strong>;
                    }
                  }
                  return <strong className="font-bold">{props.children}</strong>;
                },
              }}
            >
              {formattedSummary}
            </ReactMarkdown>
          )}
        </div>

        {/* Sentiment Trend and Stats Card */}
        {data?.stats?.time_trends && (
          <div className="flex flex-col md:flex-row gap-8 mb-10">
            {/* Line Chart */}
            <div className="md:w-1/2 w-full bg-white rounded-xl shadow p-6">
              <h4 className="text-lg font-bold mb-4">Sentiment Trend Over Time</h4>
              <Line
                data={{
                  labels: Object.keys(data.stats.time_trends).sort(),
                  datasets: [
                    ...['positive', 'negative', 'neutral'].map(sent => {
                      const color = sent === 'positive' ? '#3b82f6' : sent === 'negative' ? '#FFA07A' : '#facc15';
                      const bg = sent === 'positive' ? 'rgba(59,130,246,0.08)' : sent === 'negative' ? 'rgba(255,160,122,0.15)' : 'rgba(250,204,21,0.08)';
                      const sortedKeys = Object.keys(data.stats.time_trends).sort();
                      const values = sortedKeys.map(k => data.stats.time_trends[k][sent] || 0);
                      if (values.every(v => v === 0)) return null;
                      return {
                        label: sent.charAt(0).toUpperCase() + sent.slice(1),
                        data: values,
                        borderColor: color,
                        backgroundColor: bg,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: color,
                        pointBorderWidth: 2,
                        fill: false,
                        borderWidth: 3,
                        spanGaps: true,
                      };
                    }).filter(Boolean)
                  ],
                }}
                options={{
                  responsive: true,
                  plugins: {
                    legend: { display: true, position: 'top', labels: { boxWidth: 16, boxHeight: 16, usePointStyle: true } },
                    title: { display: false },
                    zoom: {
                      pan: {
                        enabled: true,
                        mode: 'x',
                      },
                      zoom: {
                        wheel: { enabled: true },
                        pinch: { enabled: true },
                        mode: 'x',
                      },
                      limits: {
                        x: { minRange: 5 },
                      },
                    },
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
                } as any}
              />
            </div>
            {/* Stats Card */}
            <div className="md:w-1/2 w-full bg-white rounded-xl shadow p-6 flex flex-col gap-4">
              <h4 className="text-lg font-bold mb-4">Review Stats Summary</h4>
              {/* Star Rating Distribution */}
              {data.stats.star_rating_distribution && (() => {
                const starDist = data.stats.star_rating_distribution || {};
                const starCounts = [5, 4, 3, 2, 1].map(star => starDist[star] || 0);
                const totalReviews = starCounts.reduce((a, b) => a + b, 0);
                const avgRating = totalReviews
                  ? (starCounts.reduce((sum, count, i) => sum + count * (5 - i), 0) / totalReviews)
                  : 0;
                const maxCount = Math.max(...starCounts, 1);
                return (
                  <div className="flex flex-col md:flex-row items-center gap-8 w-full">
                    {/* Left: Average and stars */}
                    <div className="flex flex-col items-center md:items-start min-w-[120px]">
                      <div className="text-5xl font-extrabold leading-none">{avgRating.toFixed(1)} <span className="text-3xl font-normal text-gray-500">out of 5</span></div>
                      <div className="flex items-center mt-2 mb-1">
                        {[1,2,3,4,5].map(i => (
                          <span key={i} className={i <= Math.round(avgRating) ? 'text-yellow-400 text-2xl' : 'text-gray-300 text-2xl'}>★</span>
                        ))}
                        <span className="ml-2 text-gray-600 text-sm">({totalReviews} reviews)</span>
                      </div>
                    </div>
                    {/* Right: Distribution bars */}
                    <div className="flex flex-col gap-1 w-full max-w-xs">
                      {[5,4,3,2,1].map((star, i) => (
                        <div key={star} className="flex items-center gap-2">
                          <span className="w-14 text-sm text-gray-700 text-right">{star} star{star > 1 ? 's' : ''}</span>
                          <div className="flex-1 h-2 rounded bg-gray-200 relative overflow-hidden">
                            <div
                              className="absolute left-0 top-0 h-2 bg-blue-500 rounded"
                              style={{ width: `${(starCounts[i] / maxCount) * 100}%` }}
                            />
                          </div>
                          <span className="w-8 text-right text-sm text-gray-700">{starCounts[i]}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}
              {/* Sentiment Confidence */}
              {data.stats.sentiment_confidence && (
                <div>
                  <div className="font-semibold mb-2 mt-4">Sentiment Model Confidence</div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    {['positive', 'neutral', 'negative'].map(sent => (
                      <div key={sent} className="flex flex-col items-center">
                        <span className={
                          sent === 'positive' ? 'text-blue-700' : sent === 'negative' ? 'text-[#D97706]' : 'text-yellow-600'
                        }>{sent.charAt(0).toUpperCase() + sent.slice(1)}</span>
                        <span>Avg: <span className="font-bold">{(data.stats.sentiment_confidence[sent]?.avg ?? 0).toFixed(2)}</span></span>
                        <span>Min: <span className="font-bold">{(data.stats.sentiment_confidence[sent]?.min ?? 0).toFixed(2)}</span></span>
                        <span>Max: <span className="font-bold">{(data.stats.sentiment_confidence[sent]?.max ?? 0).toFixed(2)}</span></span>
                        <span>Std: <span className="font-bold">{(data.stats.sentiment_confidence[sent]?.std ?? 0).toFixed(2)}</span></span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Example integration for positive and negative keywords */}
        {data && data.stats && data.stats.keyword_matched_samples && (() => {
          const posSamples = data.stats.keyword_matched_samples.positive || {};
          const negSamples = data.stats.keyword_matched_samples.negative || {};
          // Get top 10 by number of samples (descending)
          const topPos = Object.entries(posSamples)
            .sort((a, b) => (Array.isArray(b[1]) ? b[1].length : 1) - (Array.isArray(a[1]) ? a[1].length : 1))
            .slice(0, 10);
          const topNeg = Object.entries(negSamples)
            .sort((a, b) => (Array.isArray(b[1]) ? b[1].length : 1) - (Array.isArray(a[1]) ? a[1].length : 1))
            .slice(0, 10);
          // Merge and tag
          const keywords = [
            ...topPos.map(([kw]) => kw),
            ...topNeg.map(([kw]) => kw),
          ];
          const keywordSentiments = Object.fromEntries([
            ...topPos.map(([kw]) => [kw, 'positive']),
            ...topNeg.map(([kw]) => [kw, 'negative']),
          ]);
          const keywordSamples = { ...posSamples, ...negSamples };
          return (
            <KeywordChipList
              keywords={keywords}
              keywordSamples={keywordSamples}
              keywordSentiments={keywordSentiments}
            />
          );
        })()}
      </div>
    </div>
  );
} 