/**
 * ConnectionManager
 *
 * Responsibilities: health status, reconnect, retry, offline detection.
 * States: STARTING → HEALTHY / OFFLINE / ERROR
 * Exponential backoff: 1s → 2s → 4s → 8s → 10s → 10s
 *
 * This is NOT a data provider. It manages connection lifecycle only.
 */

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { healthApi } from '../../api/health';

// ── Types ─────────────────────────────────────────────────────────

export type ConnectionStatus = 'starting' | 'healthy' | 'offline' | 'error';

export interface ConnectionState {
  status: ConnectionStatus;
  /** Whether the backend is reachable */
  isOnline: boolean;
  /** Attempt count for current reconnect cycle */
  retryCount: number;
  /** Human-readable message */
  message: string;
}

const INITIAL_STATE: ConnectionState = {
  status: 'starting',
  isOnline: false,
  retryCount: 0,
  message: 'Connecting to backend...',
};

// ── Context ───────────────────────────────────────────────────────

const ConnectionContext = createContext<ConnectionState>(INITIAL_STATE);

export function useConnection(): ConnectionState {
  return useContext(ConnectionContext);
}

// ── Backoff Schedule ──────────────────────────────────────────────

const BACKOFF_SCHEDULE = [1000, 2000, 4000, 8000, 10000, 10000];

function getBackoffMs(retryCount: number): number {
  const index = Math.min(retryCount, BACKOFF_SCHEDULE.length - 1);
  return BACKOFF_SCHEDULE[index];
}

// ── Component ─────────────────────────────────────────────────────

interface ConnectionManagerProps {
  children: ReactNode;
}

export function ConnectionManager({ children }: ConnectionManagerProps) {
  const [state, setState] = useState<ConnectionState>(INITIAL_STATE);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  // ── Health check via HTTP ─────────────────────────────────────
  const checkHealth = async (): Promise<boolean> => {
    try {
      await healthApi.check();
      return true;
    } catch {
      return false;
    }
  };

  // ── Handle healthy ────────────────────────────────────────────
  const markHealthy = () => {
    if (!mountedRef.current) return;
    setState({
      status: 'healthy',
      isOnline: true,
      retryCount: 0,
      message: 'Connected',
    });
  };

  // ── Handle unhealthy ──────────────────────────────────────────
  const markOffline = (attempt: number) => {
    if (!mountedRef.current) return;
    const backoffMs = getBackoffMs(attempt);
    const nextRetry = attempt + 1;

    setState({
      status: attempt === 0 ? 'starting' : 'offline',
      isOnline: false,
      retryCount: nextRetry,
      message: attempt === 0
        ? 'Connecting to backend...'
        : `Reconnecting... (attempt ${nextRetry})`,
    });

    // Schedule next retry
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
    }
    retryTimerRef.current = setTimeout(() => {
      if (mountedRef.current) {
        pollHealth(attempt + 1);
      }
    }, backoffMs);
  };

  // ── Poll loop ─────────────────────────────────────────────────
  const pollHealth = async (attempt: number = 0) => {
    if (!mountedRef.current) return;

    const healthy = await checkHealth();
    if (!mountedRef.current) return;

    if (healthy) {
      markHealthy();
    } else {
      markOffline(attempt);
    }
  };

  // ── Listen for Tauri backend:status events ────────────────────
  useEffect(() => {
    mountedRef.current = true;

    let unlisten: (() => void) | null = null;

    const setup = async () => {
      try {
        // Try to listen for Tauri events (desktop mode)
        const { listen } = await import('@tauri-apps/api/event');
        unlisten = await listen<{ status: string; port: number; pid: number | null; message?: string }>(
          'backend:status',
          (event) => {
            if (!mountedRef.current) return;
            const payload = event.payload;

            switch (payload.status) {
              case 'healthy':
                markHealthy();
                break;
              case 'starting':
              case 'restarting':
                setState({
                  status: 'starting',
                  isOnline: false,
                  retryCount: 0,
                  message: payload.status === 'restarting'
                    ? 'Backend restarting...'
                    : 'Starting backend...',
                });
                break;
              case 'error':
                setState({
                  status: 'error',
                  isOnline: false,
                  retryCount: 0,
                  message: payload.message || 'Backend failed to start',
                });
                break;
            }
          },
        );
      } catch {
        // Not in Tauri (web mode) — fall back to HTTP polling
        pollHealth(0);
      }
    };

    setup();

    return () => {
      mountedRef.current = false;
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current);
      }
      unlisten?.();
    };
  }, []);

  // ── Render ────────────────────────────────────────────────────

  // Show splash screen when backend is starting
  if (state.status === 'starting') {
    return (
      <ConnectionContext.Provider value={state}>
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1a1a1a]">
          <div className="flex flex-col items-center gap-4">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-white/20 border-t-white" />
            <p className="text-sm text-white/50">{state.message}</p>
          </div>
        </div>
      </ConnectionContext.Provider>
    );
  }

  // Show error screen when backend fails
  if (state.status === 'error') {
    return (
      <ConnectionContext.Provider value={state}>
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1a1a1a]">
          <div className="flex flex-col items-center gap-4 max-w-md text-center">
            <div className="h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center">
              <svg className="h-6 w-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-lg font-medium text-white">Backend Unavailable</h2>
            <p className="text-sm text-white/50">{state.message}</p>
            <button
              onClick={() => {
                setState(prev => ({ ...prev, status: 'starting', message: 'Retrying...' }));
                pollHealth(0);
              }}
              className="mt-2 rounded-md bg-white/10 px-4 py-2 text-sm text-white hover:bg-white/20 transition-colors"
            >
              Retry Connection
            </button>
          </div>
        </div>
      </ConnectionContext.Provider>
    );
  }

  // Healthy — render children
  return (
    <ConnectionContext.Provider value={state}>
      {children}
    </ConnectionContext.Provider>
  );
}
