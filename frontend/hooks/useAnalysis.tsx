import { useState } from 'react';
import axios from 'axios';
import { useRouter } from 'next/router';

export function useAnalysis() {
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const router = useRouter();

  const startAnalysis = async (sku: string) => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/analyze/${sku}`);
      setJobId(res.data.job_id);
      router.push(`/processing?jobId=${res.data.job_id}`);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to start analysis.');
    } finally {
      setLoading(false);
    }
  };

  return { startAnalysis, loading, jobId, error };
} 