import React from 'react';
import { useRouter } from 'next/router';
import ProcessingDashboard from '../components/ProcessingDashboard';

export default function ProcessingPage() {
  const router = useRouter();
  const { jobId } = router.query;

  if (!jobId || typeof jobId !== 'string') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded shadow text-center">
          <p className="text-red-500">No job ID found. Please start a new analysis.</p>
        </div>
      </div>
    );
  }

  return <ProcessingDashboard jobId={jobId} />;
} 