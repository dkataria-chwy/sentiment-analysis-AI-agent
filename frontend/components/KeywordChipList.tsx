import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';

interface Props {
  keywords: string[];
  keywordSamples: { [keyword: string]: string | string[] };
  keywordSentiments?: { [keyword: string]: 'positive' | 'negative' | string };
}

export default function KeywordChipList({ keywords, keywordSamples, keywordSentiments }: Props) {
  const [openKeyword, setOpenKeyword] = useState<string | null>(null);
  const [popoverPos, setPopoverPos] = useState<{top: number, left: number, width: number, placeAbove: boolean} | null>(null);
  const btnRefs = useRef<{[kw: string]: HTMLButtonElement | null}>({});
  const popoverRef = useRef<HTMLDivElement | null>(null);

  const handleChipClick = (kw: string) => {
    if (openKeyword === kw) {
      setOpenKeyword(null);
      setPopoverPos(null);
    } else {
      const btn = btnRefs.current[kw];
      if (btn) {
        const rect = btn.getBoundingClientRect();
        const popoverWidth = 288; // w-72
        const popoverHeight = 200; // estimate
        const spaceBelow = window.innerHeight - rect.bottom;
        const placeAbove = spaceBelow < popoverHeight && rect.top > popoverHeight;
        setPopoverPos({
          top: placeAbove ? rect.top - popoverHeight - 8 : rect.bottom + 8,
          left: Math.min(rect.left, window.innerWidth - popoverWidth - 16),
          width: rect.width,
          placeAbove,
        });
      }
      setOpenKeyword(kw);
    }
  };

  // Recalculate popover position after it renders
  useEffect(() => {
    if (openKeyword && popoverRef.current && btnRefs.current[openKeyword]) {
      const btn = btnRefs.current[openKeyword];
      const pop = popoverRef.current;
      const rect = btn.getBoundingClientRect();
      const popoverRect = pop.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom;
      const placeAbove = spaceBelow < popoverRect.height && rect.top > popoverRect.height;
      setPopoverPos({
        top: placeAbove ? rect.top - popoverRect.height - 8 : rect.bottom + 8,
        left: Math.min(rect.left, window.innerWidth - popoverRect.width - 16),
        width: rect.width,
        placeAbove,
      });
    }
    // Only run after popover is rendered
    // eslint-disable-next-line
  }, [openKeyword]);

  // Close popover on outside click
  useEffect(() => {
    if (!openKeyword) return;
    function handleClick(e: MouseEvent) {
      const pop = popoverRef.current;
      const btn = openKeyword ? btnRefs.current[openKeyword] : null;
      if (pop && !pop.contains(e.target as Node) && btn && !btn.contains(e.target as Node)) {
        setOpenKeyword(null);
        setPopoverPos(null);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [openKeyword]);

  return (
    <div className="flex flex-wrap gap-2">
      {keywords.map((kw) => {
        let color = 'border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100';
        if (keywordSentiments) {
          if (keywordSentiments[kw] === 'positive') color = 'border-blue-400 bg-blue-50 text-blue-700 hover:bg-blue-100';
          if (keywordSentiments[kw] === 'negative') color = 'border-[#FFA07A] bg-[#FFF3EE] text-[#D97706] hover:bg-[#FFE5DE]';
        }
        return (
          <div key={kw} className="relative">
            <button
              ref={el => btnRefs.current[kw] = el}
              className={`px-4 py-1 rounded-full border transition focus:outline-none ${color} ${openKeyword === kw ? (keywordSentiments && keywordSentiments[kw] === 'positive' ? 'ring-2 ring-blue-300' : keywordSentiments && keywordSentiments[kw] === 'negative' ? 'ring-2 ring-[#FFA07A]' : 'ring-2 ring-blue-400') : ''}`}
              onClick={() => handleChipClick(kw)}
            >
              {kw}
            </button>
            {openKeyword === kw && popoverPos && createPortal(
              <div
                ref={popoverRef}
                className={`fixed z-50 border border-gray-200 rounded-xl shadow-lg p-4 w-72 ${keywordSentiments && keywordSentiments[kw] === 'positive' ? 'bg-blue-50' : keywordSentiments && keywordSentiments[kw] === 'negative' ? 'bg-[#FFF3EE]' : 'bg-white'}`}
                style={{
                  top: popoverPos.top,
                  left: popoverPos.left,
                  maxWidth: '90vw',
                  minWidth: 200,
                  maxHeight: 650,
                  overflowY: 'auto',
                }}
              >
                <div className="text-gray-700 text-sm">
                  {Array.isArray(keywordSamples[kw])
                    ? keywordSamples[kw].map((r, i) => <div key={i} className="mb-2">{r}</div>)
                    : keywordSamples[kw]}
                </div>
              </div>,
              document.body
            )}
          </div>
        );
      })}
    </div>
  );
} 