/**
 * ARKON Tauri Integration Layer
 * Bridges the React frontend with the Rust backend via Tauri IPC.
 *
 * This module provides:
 * 1. Type-safe IPC commands that map to Tauri invoke handlers
 * 2. Event listeners for real-time backend status updates
 * 3. File system access via Tauri plugins
 * 4. Window management utilities
 *
 * Usage:
 *   import { backend } from '@/lib/tauri';
 *   const status = await backend.getStatus();
 */

import { invoke } from '@tauri-apps/api/core';
import { listen, type UnlistenFn } from '@tauri-apps/api/event';
import { open, save } from '@tauri-apps/plugin-dialog';
import { readTextFile, writeTextFile, exists, mkdir } from '@tauri-apps/plugin-fs';
import { arch, platform, version } from '@tauri-apps/plugin-os';

// --- Types ---
export interface BackendStatus {
  running: boolean;
  pid: number | null;
  port: number;
  uptime_seconds: number | null;
  health: 'healthy' | 'unhealthy' | 'unknown';
  last_health_check: string | null;
  error: string | null;
}

export interface BackendHealth {
  status: 'ok' | 'error';
  timestamp: string;
  version: string;
  database: string;
  redis: string;
  uptime: number;
}

export interface StartBackendOptions {
  port?: number;
  debug?: boolean;
}

export interface AppConfig {
  version: string;
  backend: {
    port: number;
    host: string;
    auto_start: boolean;
    auto_restart: boolean;
    log_level: string;
  };
  frontend: {
    theme: 'dark' | 'light' | 'system';
    language: string;
    window: {
      width: number;
      height: number;
      minWidth: number;
      minHeight: number;
    };
  };
  logging: {
    level: string;
    format: string;
    backend_log: string;
    frontend_log: string;
    max_size_mb: number;
    backup_count: number;
  };
}

// --- Backend IPC Commands ---
export const backend = {
  /**
   * Start the backend process.
   * @param options - Optional configuration for the backend
   * @returns Promise that resolves when backend is healthy
   */
  async start(options?: StartBackendOptions): Promise<void> {
    await invoke('start_backend', { options: options ?? {} });
  },

  /**
   * Stop the backend process gracefully.
   */
  async stop(): Promise<void> {
    await invoke('stop_backend');
  },

  /**
   * Get the current backend status.
   */
  async getStatus(): Promise<BackendStatus> {
    return await invoke<BackendStatus>('get_backend_status');
  },

  /**
   * Check backend health via HTTP.
   */
  async checkHealth(): Promise<BackendHealth> {
    return await invoke<BackendHealth>('check_backend_health');
  },

  /**
   * Get the backend port.
   */
  async getPort(): Promise<number> {
    return await invoke<number>('get_backend_port');
  },

  /**
   * Auto-start the backend (called on app launch).
   */
  async autoStart(): Promise<void> {
    await invoke('auto_start_backend');
  },
};

// --- File System Operations ---
export const fs = {
  /**
   * Read a text file from the app's data directory.
   */
  async readText(path: string): Promise<string> {
    return await readTextFile(path);
  },

  /**
   * Write text to a file in the app's data directory.
   */
  async writeText(path: string, content: string): Promise<void> {
    await writeTextFile(path, content);
  },

  /**
   * Check if a file or directory exists.
   */
  async pathExists(path: string): Promise<boolean> {
    return await exists(path);
  },

  /**
   * Create a directory recursively.
   */
  async ensureDir(path: string): Promise<void> {
    await mkdir(path, { recursive: true });
  },
};

// --- Dialog Operations ---
export const dialog = {
  /**
   * Open a file dialog.
   */
  async openFile(options?: {
    title?: string;
    filters?: { name: string; extensions: string[] }[];
    directory?: boolean;
    multiple?: boolean;
  }): Promise<string | string[] | null> {
    return await open({
      title: options?.title,
      filters: options?.filters,
      directory: options?.directory,
      multiple: options?.multiple,
    });
  },

  /**
   * Open a save file dialog.
   */
  async saveFile(options?: {
    title?: string;
    defaultPath?: string;
    filters?: { name: string; extensions: string[] }[];
  }): Promise<string | null> {
    return await save({
      title: options?.title,
      defaultPath: options?.defaultPath,
      filters: options?.filters,
    });
  },
};

// --- System Information ---
export const system = {
  /**
   * Get the system architecture.
   */
  async getArch(): Promise<string> {
    return await arch();
  },

  /**
   * Get the platform.
   */
  async getPlatform(): Promise<string> {
    return await platform();
  },

  /**
   * Get the OS version.
   */
  async getVersion(): Promise<string> {
    return await version();
  },
};

// --- Event Listeners ---
export interface BackendStatusEvent {
  type: 'started' | 'stopped' | 'crashed' | 'restarting';
  timestamp: string;
  message: string;
}

export const events = {
  /**
   * Listen for backend status changes.
   */
  onBackendStatus(callback: (event: BackendStatusEvent) => void): Promise<UnlistenFn> {
    return listen<BackendStatusEvent>('backend-status-changed', (e) => {
      callback(e.payload);
    });
  },

  /**
   * Listen for backend log messages.
   */
  onBackendLog(callback: (log: { level: string; message: string; timestamp: string }) => void): Promise<UnlistenFn> {
    return listen<{ level: string; message: string; timestamp: string }>('backend-log', (e) => {
      callback(e.payload);
    });
  },

  /**
   * Listen for config changes.
   */
  onConfigChanged(callback: (config: AppConfig) => void): Promise<UnlistenFn> {
    return listen<AppConfig>('config-changed', (e) => {
      callback(e.payload);
    });
  },
};

// --- React Hooks ---
import { useState, useEffect, useCallback } from 'react';

/**
 * Hook to track backend status with automatic polling.
 */
export function useBackendStatus(pollIntervalMs = 5000) {
  const [status, setStatus] = useState<BackendStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    let interval: ReturnType<typeof setInterval>;

    const poll = async () => {
      try {
        const s = await backend.getStatus();
        if (mounted) {
          setStatus(s);
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to get backend status');
          setLoading(false);
        }
      }
    };

    poll();
    interval = setInterval(poll, pollIntervalMs);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [pollIntervalMs]);

  const start = useCallback(async (options?: StartBackendOptions) => {
    setLoading(true);
    try {
      await backend.start(options);
      const s = await backend.getStatus();
      setStatus(s);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start backend');
    } finally {
      setLoading(false);
    }
  }, []);

  const stop = useCallback(async () => {
    setLoading(true);
    try {
      await backend.stop();
      const s = await backend.getStatus();
      setStatus(s);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop backend');
    } finally {
      setLoading(false);
    }
  }, []);

  return { status, loading, error, start, stop };
}

/**
 * Hook to listen for backend status events.
 */
export function useBackendEvents() {
  const [backendEvents, setBackendEvents] = useState<BackendStatusEvent[]>([]);

  useEffect(() => {
    let unlisten: UnlistenFn | null = null;

    const setup = async () => {
      unlisten = await events.onBackendStatus((e) => {
        setBackendEvents((prev) => [...prev.slice(-49), e]); // Keep last 50 events
      });
    };

    setup();

    return () => {
      unlisten?.();
    };
  }, []);

  return backendEvents;
}
