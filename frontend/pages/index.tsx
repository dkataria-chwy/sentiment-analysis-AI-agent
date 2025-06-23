import React, { useState } from 'react';
import axios from 'axios';
import { useRouter } from 'next/router';

export default function Home() {
  const [sku, setSku] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const validateSku = (value: string) => {
    if (!value.trim()) return 'SKU is required.';
    if (!/^[\w\-]+$/.test(value.trim())) return 'Invalid SKU format.';
    return '';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const err = validateSku(sku);
    setError(err);
    if (err) return;
    setLoading(true);
    try {
      const res = await axios.post(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/analyze/${sku}`);
      router.push(`/processing?jobId=${res.data.job_id}`);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to start analysis.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Card/Tile centered horizontally, not vertically */}
      <div className="flex justify-center">
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-200 shadow-2xl p-10 w-full max-w-xl">
          <h2 className="text-xl font-semibold mb-2">Start New Product Analysis</h2>
          <p className="mb-4 text-gray-500">
            Just type in the product name (for example, "131886") and we'll analyze the customer reviews.
          </p>
          <label className="block text-sm font-medium text-gray-700 mb-1">Product part number</label>
          <textarea
            className="w-full border border-gray-300 rounded-lg px-4 py-3 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., 131886"
            rows={4}
            value={sku}
            onChange={e => setSku(e.target.value)}
            disabled={loading}
          />
          <div className="text-xs text-gray-400 mb-4">
            Be specific about what you want to research for better results
          </div>
          {error && <div className="text-red-500 text-sm mb-2">{error}</div>}
          {/* Animated colorful border on the button itself */}
          <div className="relative w-full flex justify-center mb-2">
            <div
              className="relative rounded-full overflow-hidden animate-gradient-move"
              style={{
                padding: '4px',
                background: 'linear-gradient(90deg, #3b82f6, #a21caf,rgb(41, 167, 22),rgb(236, 199, 16) ,rgb(236, 100, 16), #ec4899, #3b82f6)',
                backgroundSize: '400% 400%',
              }}
            >
              <button
                type="submit"
                className="relative bg-white text-blue-700 px-8 py-2 rounded-full font-semibold hover:bg-blue-50 transition border-none focus:outline-none z-10"
                disabled={loading}
                style={{ minWidth: 200 }}
              >
                {loading ? 'Analyzing...' : 'Start AI agent'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
} 