import '../styles/globals.css';
import type { AppProps } from 'next/app';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div className="dotted-bg">
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
  );
} 