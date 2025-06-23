import React from 'react';

interface Props {
  steps: string[];
  currentStep: number;
}

export default function ProgressBar({ steps, currentStep }: Props) {
  const percent = Math.min((currentStep / steps.length) * 100, 100);
  return (
    <div>
      <div className="flex justify-between mb-2">
        {steps.map((step, idx) => (
          <div key={step} className={`text-xs ${idx <= currentStep - 1 ? 'text-blue-600 font-bold' : 'text-gray-400'}`}>{step}</div>
        ))}
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className="bg-blue-600 h-3 rounded-full transition-all"
          style={{ width: `${percent}%` }}
        ></div>
      </div>
    </div>
  );
} 