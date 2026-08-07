/**
 * ARKON Desktop Application Entry Point
 *
 * Initializes the React application with Tauri integration,
 * configuration, and backend management.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App } from './App';
import { appBootstrap } from './lib/bootstrap';
import { ErrorBoundary } from './lib/crash-handler';

// --- Query Client Configuration ---
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// --- Application Bootstrap ---
async function main() {
  console.log('[ARKON] Starting application...');

  // Initialize the application
  const state = await appBootstrap.init({
    onStateChange: (state) => {
      console.log('[ARKON] State changed:', state);
    },
  });

  if (state.error) {
    console.error('[ARKON] Initialization error:', state.error);
  }

  // Render the application
  const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
  );

  root.render(
    <React.StrictMode>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <App />
        </QueryClientProvider>
      </ErrorBoundary>
    </React.StrictMode>
  );

  // Handle window close
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', async () => {
      await appBootstrap.shutdown();
    });
  }
}

// Start the application
main().catch((error) => {
  console.error('[ARKON] Fatal error:', error);
});
