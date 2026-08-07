/**
 * ARKON Backend Status Banner
 *
 * Displays a banner when the backend is not running,
 * providing status information and recovery actions.
 */

import React from 'react';
import { backend, type BackendStatus } from '../../lib/tauri';

interface BackendStatusBannerProps {
  status: BackendStatus;
}

export function BackendStatusBanner({ status }: BackendStatusBannerProps) {
  const [retrying, setRetrying] = React.useState(false);

  const handleRetry = async () => {
    setRetrying(true);
    try {
      await backend.autoStart();
    } catch (err) {
      console.error('Failed to restart backend:', err);
    } finally {
      setRetrying(false);
    }
  };

  if (status.running) {
    return null;
  }

  return (
    <div className="bg-yellow-900/50 border-b border-yellow-700 px-4 py-2 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
        <span className="text-sm text-yellow-200">
          {status.error
            ? `Backend Error: ${status.error}`
            : 'Backend is not running'}
        </span>
      </div>
      <button
        onClick={handleRetry}
        disabled={retrying}
        className="px-3 py-1 text-xs bg-yellow-700 hover:bg-yellow-600 text-yellow-100 rounded disabled:opacity-50"
      >
        {retrying ? 'Starting...' : 'Start Backend'}
      </button>
    </div>
  );
}
