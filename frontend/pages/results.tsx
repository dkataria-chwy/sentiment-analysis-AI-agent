import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import ResultsDashboard from '../components/ResultsDashboard';
import axios from 'axios';

function Spinner({ text = "Generating executive summary..." }) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <span role="img" aria-label="AI" className="animate-bounce text-6xl">✨</span>
      <div
        className="mt-4 font-semibold text-lg bg-clip-text text-transparent"
        style={{
          backgroundImage:
            'linear-gradient(90deg,rgb(49, 39, 239),rgb(23, 74, 155),rgb(102, 168, 249))'
        }}
      >
        {text}
      </div>
    </div>
  );
}

export default function ResultsPage() {
  const router = useRouter();
  const { jobId } = router.query;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState('');

  // Toggle dancing dots overlay during loading/summaryLoading
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (loading || summaryLoading) {
      // Target the results card (or shell while loading) so dots animate within that area
      const targetId = loading ? 'results-card-shell' : 'results-dashboard-card';
      window.dispatchEvent(new CustomEvent('dots:start', { detail: { region: 'element', elementId: targetId } }));
      // Hide dotted texture on the root wrapper while loading
      const root = document.querySelector('.dotted-bg');
      root?.classList.add('no-dots');
    } else {
      window.dispatchEvent(new Event('dots:stop'));
      // Restore dotted texture on the root wrapper when done
      const root = document.querySelector('.dotted-bg');
      root?.classList.remove('no-dots');
    }
    return () => {
      window.dispatchEvent(new Event('dots:stop'));
      const root = document.querySelector('.dotted-bg');
      root?.classList.remove('no-dots');
    };
  }, [loading, summaryLoading]);

  useEffect(() => {
    if (!jobId || typeof jobId !== 'string') return;
    setLoading(true);
    setError('');
    setSummaryError('');
    setSummaryLoading(false);
    axios.get(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/results/${jobId}`)
      .then(res => {
        setData(res.data);
        setSummaryLoading(true);
        // Fetch the real summary
        return axios.get(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/summary/${jobId}`);
      })
      .then(res => {
        setData(prev => ({ ...prev, summary: res.data.summary, stats: res.data.stats }));
        setSummaryLoading(false);
      })
      .catch((err) => {
        if (!data) setError('Failed to fetch results.');
        setSummaryError('Failed to fetch executive summary.');
        setSummaryLoading(false);
      })
      .finally(() => setLoading(false));
  }, [jobId]);

  if (!jobId || typeof jobId !== 'string') {
    return <div className="min-h-screen flex items-center justify-center">No job ID found.</div>;
  }
  if (loading) {
    return (
      <div className="relative min-h-screen no-dots">
        {/* Target region for animated dots: positioned where the final card will sit */}
        <div
          id="results-card-shell"
          className="pointer-events-none absolute left-1/2 -translate-x-1/2 top-[16vh] w-full max-w-7xl h-[680px] md:h-[720px]"
        />
        {/* Center the spinner vertically */}
        <div className="absolute inset-0 flex items-center justify-center mt-[-4vh]">
          <Spinner text="Generating executive summary..." />
        </div>
      </div>
    );
  }
  if (error) {
    return <div className="min-h-screen flex items-center justify-center text-red-500">{error}</div>;
  }
  return <ResultsDashboard data={data} summaryLoading={summaryLoading} summaryError={summaryError} />;
} 