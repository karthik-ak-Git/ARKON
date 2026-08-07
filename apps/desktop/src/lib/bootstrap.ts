/**
 * ARKON Application Bootstrap
 *
 * Initializes the application with:
 * 1. Configuration loading
 * 2. Backend auto-start
 * 3. Crash handler setup
 * 4. Auto-updater initialization
 * 5. Logging setup
 */

import { configManager } from './config';
import { backend, type BackendStatus } from './tauri';
import { crashHandler } from './crash-handler';
import { autoUpdater } from './updater';

// --- App State ---
export interface AppState {
  initialized: boolean;
  backend: BackendStatus | null;
  config: {
    settings: any;
    providers: any;
    plugins: any;
  } | null;
  error: string | null;
}

// --- App Bootstrap ---
export class AppBootstrap {
  private state: AppState = {
    initialized: false,
    backend: null,
    config: null,
    error: null,
  };

  private onStateChange: ((state: AppState) => void) | null = null;

  /**
   * Initialize the application.
   */
  async init(options?: {
    onStateChange?: (state: AppState) => void;
  }): Promise<AppState> {
    this.onStateChange = options?.onStateChange ?? null;

    try {
      this.updateState({ initialized: false, error: null });

      // Step 1: Initialize configuration
      console.log('[AppBootstrap] Initializing configuration...');
      await configManager.init();
      const settings = await configManager.readSettings();
      const providers = await configManager.readProviders();
      const plugins = await configManager.readPlugins();

      this.updateState({
        config: { settings, providers, plugins },
      });

      // Step 2: Initialize crash handler
      console.log('[AppBootstrap] Initializing crash handler...');
      crashHandler.init();

      // Step 3: Auto-start backend
      if (settings.backend.auto_start) {
        console.log('[AppBootstrap] Auto-starting backend...');
        try {
          await backend.autoStart();
          const status = await backend.getStatus();
          this.updateState({ backend: status });
        } catch (error) {
          console.warn('[AppBootstrap] Backend auto-start failed:', error);
          this.updateState({
            error: `Backend auto-start failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
          });
        }
      }

      // Step 4: Initialize auto-updater
      console.log('[AppBootstrap] Initializing auto-updater...');
      autoUpdater.setCurrentVersion(settings.version || '1.0.0');
      if (settings.updates?.auto_check) {
        autoUpdater.init({
          checkIntervalMs: (settings.updates?.check_interval_hours ?? 24) * 60 * 60 * 1000,
        });
      }

      // Step 5: Mark as initialized
      this.updateState({ initialized: true });
      console.log('[AppBootstrap] Application initialized successfully');

      return this.state;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Initialization failed';
      console.error('[AppBootstrap] Initialization failed:', error);
      this.updateState({
        initialized: true, // Mark as initialized even on error so UI can render
        error: errorMessage,
      });
      return this.state;
    }
  }

  /**
   * Update the application state.
   */
  private updateState(partial: Partial<AppState>): void {
    this.state = { ...this.state, ...partial };
    this.onStateChange?.(this.state);
  }

  /**
   * Get the current application state.
   */
  getState(): AppState {
    return { ...this.state };
  }

  /**
   * Restart the backend.
   */
  async restartBackend(): Promise<void> {
    try {
      await backend.stop();
      await new Promise((resolve) => setTimeout(resolve, 1000));
      await backend.autoStart();
      const status = await backend.getStatus();
      this.updateState({ backend: status });
    } catch (error) {
      console.error('[AppBootstrap] Backend restart failed:', error);
      this.updateState({
        error: `Backend restart failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    }
  }

  /**
   * Shutdown the application gracefully.
   */
  async shutdown(): Promise<void> {
    console.log('[AppBootstrap] Shutting down...');
    autoUpdater.destroy();

    try {
      const status = await backend.getStatus();
      if (status.running) {
        await backend.stop();
      }
    } catch (error) {
      console.warn('[AppBootstrap] Error during shutdown:', error);
    }
  }
}

// Singleton instance
export const appBootstrap = new AppBootstrap();
