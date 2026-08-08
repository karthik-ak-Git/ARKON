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
}

export interface BackendHealth {
  healthy: boolean;
  message: string;
}

export interface BackendStatusPayload {
  status: 'starting' | 'healthy' | 'error' | 'restarting';
  port: number;
  pid: number | null;
  message?: string;
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
   */
  async start(): Promise<BackendStatus> {
    return await invoke<BackendStatus>('start_backend');
  },

  /**
   * Stop the backend process gracefully.
   */
  async stop(): Promise<BackendStatus> {
    return await invoke<BackendStatus>('stop_backend');
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
};

// --- File System Operations ---
export const fs = {
  async readText(path: string): Promise<string> {
    return await readTextFile(path);
  },

  async writeText(path: string, content: string): Promise<void> {
    await writeTextFile(path, content);
  },

  async pathExists(path: string): Promise<boolean> {
    return await exists(path);
  },

  async ensureDir(path: string): Promise<void> {
    await mkdir(path, { recursive: true });
  },
};

// --- Dialog Operations ---
export const dialog = {
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
  async getArch(): Promise<string> {
    return await arch();
  },

  async getPlatform(): Promise<string> {
    return await platform();
  },

  async getVersion(): Promise<string> {
    return await version();
  },
};

// --- Event Listeners ---
export const events = {
  /**
   * Listen for backend status changes emitted by Tauri at startup.
   * Events: 'backend:status' with BackendStatusPayload
   */
  onBackendStatus(callback: (payload: BackendStatusPayload) => void): Promise<UnlistenFn> {
    return listen<BackendStatusPayload>('backend:status', (e) => {
      callback(e.payload);
    });
  },
};

// --- React Hooks ---
import { useState, useEffect } from 'react';

/**
 * Hook that tracks backend status via Tauri events (no polling).
 * Tauri auto-starts the backend at launch and emits status events.
 */
export function useBackendStatus() {
  const [status, setStatus] = useState<BackendStatusPayload>({
    status: 'starting',
    port: 8000,
    pid: null,
  });

  useEffect(() => {
    let unlisten: UnlistenFn | null = null;

    const setup = async () => {
      unlisten = await events.onBackendStatus((payload) => {
        setStatus(payload);
      });
    };

    setup();

    return () => {
      unlisten?.();
    };
  }, []);

  const isHealthy = status.status === 'healthy';
  const isStarting = status.status === 'starting' || status.status === 'restarting';
  const isError = status.status === 'error';

  return { status, isHealthy, isStarting, isError };
}

/**
 * Hook to listen for backend status events (for logging/debugging).
 */
export function useBackendEvents() {
  const [events_list, setEvents] = useState<BackendStatusPayload[]>([]);

  useEffect(() => {
    let unlisten: UnlistenFn | null = null;

    const setup = async () => {
      unlisten = await events.onBackendStatus((e) => {
        setEvents((prev) => [...prev.slice(-49), e]);
      });
    };

    setup();

    return () => {
      unlisten?.();
    };
  }, []);

  return events_list;
}
