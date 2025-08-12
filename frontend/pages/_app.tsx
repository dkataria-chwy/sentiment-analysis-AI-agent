import React from 'react';
import '../styles/globals.css';
import type { AppProps } from 'next/app';
import DancingDotsOverlay from '../components/DancingDotsOverlay';
import { useRouter } from 'next/router';

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const path = router.pathname;
  const isOverlayPage = path === '/' || path === '/results'; // animated dots only on home + results

  return (
    <div className={'dotted-bg'}>
      <div className="gradient-overlay" />
      <div className="relative z-10">
        <div className="w-full pt-12 pb-6 text-center">
          <h1 className="text-4xl font-bold flex items-center justify-center gap-2 mb-2">
            <span role="img" aria-label="paw">🐾</span>
            Sentiment Analysis AI Agent
          </h1>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Your intelligent AI agent for customer review sentiment analysis.
          </p>
        </div>
        <Component {...pageProps} />
      </div>
      {isOverlayPage && <DotsOverlayBridge />}
    </div>
  );
} 

// Lightweight bridge: listens to window events to toggle the overlay
function DotsOverlayBridge() {
  const [active, setActive] = React.useState(false);
  const [region, setRegion] = React.useState<'full' | 'centerBand' | 'element'>('centerBand');
  const [elementId, setElementId] = React.useState<string | undefined>(undefined);

  React.useEffect(() => {
    const onStart = (e: Event) => {
      setActive(true);
      if (e instanceof CustomEvent && e.detail) {
        const { region: r, elementId: id } = e.detail as { region?: 'full' | 'centerBand' | 'element'; elementId?: string };
        if (r) setRegion(r);
        if (id) setElementId(id);
      } else {
        setRegion('centerBand');
        setElementId(undefined);
      }
    };
    const onStop = () => setActive(false);
    window.addEventListener('dots:start', onStart as EventListener);
    window.addEventListener('dots:stop', onStop as EventListener);
    return () => {
      window.removeEventListener('dots:start', onStart as EventListener);
      window.removeEventListener('dots:stop', onStop as EventListener);
    };
  }, []);
  return <DancingDotsOverlay active={active} region={region} elementId={elementId} />;
}

// (GradientOverlayBridge removed; gradient is always visible on all pages.)