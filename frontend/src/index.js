import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/globals.css';
import App from './App';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';
import { ThemeProvider } from './contexts/ThemeContext';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Error Fallback Component
const ErrorFallback = ({ error, resetErrorBoundary }) => {
  return (
    <div className="min-h-screen bg-background-dark text-text-dark flex items-center justify-center p-4">
      <div className="glass-card p-8 max-w-md w-full text-center">
        <div className="text-danger text-4xl mb-4">⚠️</div>
        <h2 className="text-2xl font-orbitron font-bold text-primary mb-4">
          System Malfunction
        </h2>
        <p className="text-text-dark/80 mb-6">
          The Sigma AI platform encountered an error. Our engineers have been notified.
        </p>
        <div className="bg-card-dark/50 p-4 rounded-lg mb-6 text-left">
          <code className="text-sm text-danger">{error.message}</code>
        </div>
        <button
          onClick={resetErrorBoundary}
          className="bg-primary hover:bg-primary-dark text-black font-semibold py-2 px-6 rounded-lg transition-all duration-300 transform hover:scale-105"
        >
          Reinitialize System
        </button>
      </div>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
