import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import ResultsDashboard from '../components/ResultsDashboard';
import axios from 'axios';

function Spinner({ text = "Generating executive summary..." }) {
  return (
    <div className="flex flex-col items-center justify-center py-8">
      <span role="img" aria-label="AI" className="animate-bounce text-6xl">✨</span>
      <div className="mt-4 text-blue-700 font-semibold text-lg">{text}</div>
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
      <div className="min-h-screen flex items-center justify-center">
        <Spinner text="Generating executive summary..." />
      </div>
    );
  }
  if (error) {
    return <div className="min-h-screen flex items-center justify-center text-red-500">{error}</div>;
  }
  return <ResultsDashboard data={data} summaryLoading={summaryLoading} summaryError={summaryError} />;
} 