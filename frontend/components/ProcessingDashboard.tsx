import React, { useEffect, useState, useRef } from 'react';

const STEPS = [
  'FetchReviews',
  'CleanText',
  'EmbedBatch',
  'ClassifyBatch',
  'AspectExtract',
  'KeywordExtract',
  'StatsBuild',
  'GptSummary',
];

const CLEAN_TEXT_SUBSTEPS = [
  'html',
  'encoding',
  'emoji',
  'control',
  'whitespace',
];

interface Props {
  jobId: string;
}

export default function ProcessingDashboard({ jobId }: Props) {
  const [currentStep, setCurrentStep] = useState(0);
  const [status, setStatus] = useState('processing');
  const [logs, setLogs] = useState<string[]>([]);
  const [cancelled, setCancelled] = useState(false);
  const [subStepProgress, setSubStepProgress] = useState<{[key: string]: string}>({});
  const lastLoggedStep = useRef<number>(0);

  useEffect(() => {
    if (cancelled) {
      setStatus('cancelled');
      setLogs(logs => [...logs, 'Analysis cancelled by user.']);
      return;
    }
    if (status === 'complete' || status === 'cancelled') return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/status/${jobId}`);
        if (!res.ok) return;
        const data = await res.json();
        let stepNum = data.step;
        // Map step 3.5 to AspectExtract (index 4)
        if (stepNum === 3.5) stepNum = 4;
        if (typeof stepNum === 'number') {
          if (stepNum > lastLoggedStep.current) {
            setLogs(logs => [
              ...logs,
              `Step ${stepNum}: ${STEPS[stepNum-1]} finished.`,
              `Step ${stepNum+1}: ${STEPS[stepNum]} started...`
            ]);
            lastLoggedStep.current = stepNum;
          }
          setCurrentStep(stepNum);
        }
        if (data.status) setStatus(data.status);
        if (data.status === 'complete') {
          setLogs(logs => [...logs, 'Analysis complete! Redirecting to results...']);
          clearInterval(interval);
          setTimeout(() => {
            window.location.href = `/results?jobId=${jobId}`;
          }, 1500);
        }
      } catch (e) {
        // Optionally handle error
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [jobId, cancelled, status]);

  useEffect(() => {
    if (currentStep === 1 && status !== 'complete') {
      // All sub-steps in progress during CleanText
      setSubStepProgress(Object.fromEntries(CLEAN_TEXT_SUBSTEPS.map(s => [s, 'in_progress'])));
    } else if (currentStep > 1 || status === 'complete') {
      // All sub-steps done after CleanText
      setSubStepProgress(Object.fromEntries(CLEAN_TEXT_SUBSTEPS.map(s => [s, 'done'])));
    } else {
      setSubStepProgress({});
    }
  }, [currentStep, status]);

  const handleCancel = () => {
    setCancelled(true);
  };

  const percent = Math.min((currentStep / STEPS.length) * 100, 100);

  return (
    <div className="max-w-3xl mx-auto mt-8 p-8 bg-white rounded-2xl border border-gray-200 shadow-2xl flex flex-col md:flex-row gap-8">
      {/* Modern Vertical Stepper */}
      <div className="flex-1 flex flex-col items-center">
        {/* Header */}
        <h2 className="text-xl font-bold mb-2 text-center">Analyzing Reviews...</h2>
        {/* Segmented Capsule Progress Bar */}
        <div className="flex items-center justify-center mb-4">
          {STEPS.map((_, idx) => (
            <div
              key={idx}
              className={`h-3 mx-0.5 rounded-full transition-all duration-300 ${idx < currentStep ? 'bg-gradient-to-r from-green-400 via-blue-400 to-purple-500' : 'bg-gray-200'} ${currentStep === 1 && idx !== 1 ? 'opacity-30' : ''}`}
              style={{ width: 32, minWidth: 24, opacity: idx < currentStep ? 1 : 0.5 }}
            ></div>
          ))}
        </div>
        {/* Workflow (Vertical Stepper) */}
        <div className="flex flex-col items-center w-full md:w-1/3 mb-4">
          {STEPS.map((step, idx) => {
            const isCompleted = idx < currentStep;
            const isCurrent = idx === currentStep;
            // Fade other steps when CleanText is active
            const faded = currentStep === 1 && idx !== 1;
            return (
              <div key={step} className={`flex items-center relative z-10 mb-6 last:mb-0 w-full transition-all duration-300 ${faded ? 'opacity-30 blur-[1px]' : ''}`}> 
                <div className="flex flex-col items-center mr-3" style={{minWidth: 32}}>
                  <div className={`flex items-center justify-center transition-all duration-300
                    ${isCurrent ? 'w-10 h-10 bg-blue-500 border-4 border-blue-300 text-white text-lg shadow-lg scale-110' :
                      isCompleted ? 'w-7 h-7 bg-green-500 border-2 border-green-300 text-white text-base' :
                      'w-7 h-7 bg-gray-200 border-2 border-gray-300 text-gray-400 text-base'}
                    rounded-full font-bold mb-1`}
                  >
                    {isCompleted ? '✓' : idx + 1}
                  </div>
                  {/* Connector line for all but last step */}
                  {idx < STEPS.length - 1 && (
                    <div className={`flex-1 w-1 ${isCompleted ? 'bg-green-400' : isCurrent ? 'bg-blue-400' : 'bg-gray-200'} opacity-60`} style={{minHeight: 24}}></div>
                  )}
                </div>
                <span className={`text-base transition-all duration-300
                  ${isCompleted ? 'text-green-700' : isCurrent ? 'text-blue-700 font-semibold' : 'text-gray-400'}`}>{step}</span>
                {/* Show sub-steps for CleanText */}
                {currentStep === 1 && idx === 1 && (
                  <div className="ml-6 flex flex-col gap-2 w-full">
                    {CLEAN_TEXT_SUBSTEPS.map((sub) => (
                      <div key={sub} className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${subStepProgress[sub] === 'done' ? 'bg-green-400' : subStepProgress[sub] === 'in_progress' ? 'bg-blue-300 animate-pulse' : 'bg-gray-200'}`}></div>
                        <span className={`text-sm ${subStepProgress[sub] === 'done' ? 'text-green-700' : subStepProgress[sub] === 'in_progress' ? 'text-blue-700' : 'text-gray-400'}`}>{sub}</span>
                        {subStepProgress[sub] === 'in_progress' && <span className="text-xs text-blue-400 animate-pulse ml-2">In progress...</span>}
                        {subStepProgress[sub] === 'done' && <span className="text-xs text-green-500 ml-2">Done</span>}
                        {(!subStepProgress[sub] || subStepProgress[sub] === 'pending') && <span className="text-xs text-gray-400 ml-2">Pending</span>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
        {/* Step execution/status */}
        <div className="flex justify-between items-center w-full mb-2">
          <span className="text-gray-600">Status: <span className={status === 'complete' ? 'text-green-600' : status === 'cancelled' ? 'text-red-500' : 'text-blue-600'}>{status}</span></span>
        </div>
        {/* Log window */}
        <div className="bg-gray-50 rounded p-3 h-32 overflow-y-auto text-xs font-mono border border-gray-200 mb-2 w-full max-w-md mx-auto">
          {logs.map((log, i) => <div key={i}>{log}</div>)}
        </div>
        {/* Cancel button and status message */}
        <div className="flex justify-center">
          <button
            className="bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600"
            onClick={handleCancel}
          >
            Cancel Analysis
          </button>
        </div>
      </div>
    </div>
  );
}