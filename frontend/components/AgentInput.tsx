import React, { useState } from 'react';
import { useAnalysis } from '../hooks/useAnalysis';

export default function AgentInput() {
  const [sku, setSku] = useState('');
  const [error, setError] = useState('');
  const { startAnalysis, loading } = useAnalysis();

  const validateSku = (value: string) => {
    if (!value.trim()) return 'SKU is required.';
    if (!/^[\w\-]+$/.test(value.trim())) return 'Invalid SKU format.';
    return '';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const err = validateSku(sku);
    setError(err);
    if (!err) {
      await startAnalysis(sku);
    }
  };

  return (
    <div className="max-w-lg mx-auto mt-20 p-8 bg-white rounded-xl shadow-lg">
      <h1 className="text-2xl font-bold mb-2">Customer Sentiment Analysis Agent</h1>
      <p className="mb-6 text-gray-600">Enter a product SKU to analyze customer sentiment from thousands of reviews. The agent will fetch, process, and summarize insights for you.</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          className="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g. ABC-123"
          value={sku}
          onChange={e => setSku(e.target.value)}
          disabled={loading}
        />
        {error && <div className="text-red-500 text-sm">{error}</div>}
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </form>
    </div>
  );
} 