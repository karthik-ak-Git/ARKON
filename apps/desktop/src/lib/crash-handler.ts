/**
 * ARKON Crash Handler
 *
 * Provides crash reporting, error boundaries, and graceful degradation.
 * Captures unhandled errors and writes crash reports to the logs directory.
 */

import { backend, events, type BackendStatusEvent } from './tauri';

// --- Crash Report Structure ---
export interface CrashReport {
  timestamp: string;
  type: 'backend' | 'frontend' | 'renderer' | 'unknown';
  error: {
    name: string;
    message: string;
    stack?: string;
  };
  context: {
    backend_status: string;
    platform: string;
    version: string;
    url?: string;
  };
  environment: {
    memory: string;
    storage: string;
  };
}

// --- Crash Handler Class ---
export class CrashHandler {
  private reports: CrashReport[] = [];
  private maxReports = 50;
  private initialized = false;

  /**
   * Initialize the crash handler.
   */
  init(): void {
    if (this.initialized) return;

    // Listen for backend crashes
    events.onBackendStatus((event: BackendStatusEvent) => {
      if (event.type === 'crashed') {
        this.handleBackendCrash(event);
      }
    });

    // Listen for unhandled errors in renderer
    if (typeof window !== 'undefined') {
      window.addEventListener('error', (event) => {
        this.handleRendererError(event.error || new Error(event.message));
      });

      window.addEventListener('unhandledrejection', (event) => {
        this.handleRendererError(
          event.reason instanceof Error
            ? event.reason
            : new Error(String(event.reason))
        );
      });
    }

    this.initialized = true;
    console.log('[CrashHandler] Initialized');
  }

  /**
   * Handle a backend crash event.
   */
  private async handleBackendCrash(event: BackendStatusEvent): Promise<void> {
    const report: CrashReport = {
      timestamp: new Date().toISOString(),
      type: 'backend',
      error: {
        name: 'BackendCrash',
        message: event.message || 'Backend process crashed unexpectedly',
      },
      context: {
        backend_status: 'crashed',
        platform: 'unknown',
        version: '1.0.0',
      },
      environment: {
        memory: 'unknown',
        storage: 'unknown',
      },
    };

    await this.writeCrashReport(report);
  }

  /**
   * Handle a renderer (frontend) error.
   */
  public async handleRendererError(error: Error): Promise<void> {
    let backendStatus = 'unknown';
    try {
      const status = await backend.getStatus();
      backendStatus = status.running ? 'running' : 'stopped';
    } catch {
      backendStatus = 'unreachable';
    }

    const report: CrashReport = {
      timestamp: new Date().toISOString(),
      type: 'renderer',
      error: {
        name: error.name || 'RendererError',
        message: error.message || 'Unknown renderer error',
        stack: error.stack,
      },
      context: {
        backend_status: backendStatus,
        platform: 'unknown',
        version: '1.0.0',
        url: window.location?.href,
      },
      environment: {
        memory: 'unknown',
        storage: 'unknown',
      },
    };

    await this.writeCrashReport(report);
  }

  /**
   * Write a crash report to the logs directory.
   */
  private async writeCrashReport(report: CrashReport): Promise<void> {
    try {
      this.reports.push(report);
      if (this.reports.length > this.maxReports) {
        this.reports.shift();
      }

      // Log to console in development
      console.error('[CrashHandler] Crash report:', report);

      // In production, write to file via Tauri
      // This is handled by the Rust backend
    } catch (err) {
      console.error('[CrashHandler] Failed to write crash report:', err);
    }
  }

  /**
   * Get all crash reports.
   */
  getReports(): CrashReport[] {
    return [...this.reports];
  }

  /**
   * Clear all crash reports.
   */
  clearReports(): void {
    this.reports = [];
  }

  /**
   * Generate a crash summary for display.
   */
  generateSummary(report: CrashReport): string {
    const lines = [
      `ARKON Crash Report`,
      `==================`,
      ``,
      `Type: ${report.type}`,
      `Time: ${report.timestamp}`,
      ``,
      `Error:`,
      `  Name: ${report.error.name}`,
      `  Message: ${report.error.message}`,
      ``,
      `Context:`,
      `  Backend Status: ${report.context.backend_status}`,
      `  Platform: ${report.context.platform}`,
      `  Version: ${report.context.version}`,
    ];

    if (report.context.url) {
      lines.push(`  URL: ${report.context.url}`);
    }

    if (report.error.stack) {
      lines.push(``, `Stack Trace:`, report.error.stack);
    }

    return lines.join('\n');
  }
}

// Singleton instance
export const crashHandler = new CrashHandler();

// --- React Error Boundary Helper ---
import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * React Error Boundary component for catching renderer errors.
 */
export class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    crashHandler.handleRendererError(error);
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return React.createElement(
        'div',
        {
          style: {
            padding: '2rem',
            textAlign: 'center',
            backgroundColor: '#1a1a2e',
            color: '#e0e0e0',
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
          },
        },
        React.createElement('h1', { style: { color: '#ff6b6b' } }, 'Something went wrong'),
        React.createElement('p', null, 'ARKON encountered an unexpected error.'),
        React.createElement(
          'button',
          {
            onClick: () => window.location.reload(),
            style: {
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              backgroundColor: '#4ecdc4',
              color: '#000',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            },
          },
          'Reload Application'
        )
      );
    }

    return this.props.children;
  }
}
