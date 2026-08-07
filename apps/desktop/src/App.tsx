/**
 * ARKON App Component
 *
 * Root component that handles:
 * 1. Application initialization state
 * 2. Backend status monitoring
 * 3. Layout and routing
 */

import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { backend, useBackendStatus } from './lib/tauri';
import { Sidebar } from './components/layout/Sidebar';
import { MainWorkspace } from './components/layout/MainWorkspace';
import { CommandBox } from './components/layout/CommandBox';
import { BackendStatusBanner } from './components/layout/BackendStatusBanner';

export function App() {
  const { status, loading, error } = useBackendStatus(10000);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    // App is initialized once we have the first status check
    if (status !== null || error !== null) {
      setInitialized(true);
    }
  }, [status, error]);

  // Show loading screen during initialization
  if (!initialized || loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[var(--bg-primary)]">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin" />
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">
            ARKON
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-2">
            Initializing...
          </p>
        </div>
      </div>
    );
  }

  // Show error screen if backend failed to start
  if (error && !status?.running) {
    return (
      <div className="flex items-center justify-center h-screen bg-[var(--bg-primary)]">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 mx-auto mb-4 text-red-500">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">
            Backend Error
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-2 mb-4">
            {error}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-[var(--accent-primary)] text-white rounded hover:opacity-90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-primary)]">
      {/* Backend Status Banner */}
      {status && !status.running && (
        <BackendStatusBanner status={status} />
      )}

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Command Box */}
        <CommandBox />

        {/* Main Workspace */}
        <MainWorkspace />
      </div>
    </div>
  );
}
