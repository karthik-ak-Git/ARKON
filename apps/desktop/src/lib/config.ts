/**
 * ARKON Configuration Manager
 *
 * Handles reading/writing configuration files from the app's data directory.
 * Configuration is stored in {LOCALAPPDATA}/arkon/config/
 *
 * On first launch:
 * 1. Creates default config directory structure
 * 2. Copies default settings from bundled templates
 * 3. Migrates config from previous versions if needed
 */

import { exists, readTextFile, writeTextFile, mkdir } from '@tauri-apps/plugin-fs';
import { appDataDir, join } from '@tauri-apps/api/path';

// --- Default Configurations ---
export const DEFAULT_SETTINGS = {
  version: '1.0.0',
  backend: {
    port: 8000,
    host: '127.0.0.1',
    auto_start: true,
    auto_restart: true,
    log_level: 'info',
  },
  frontend: {
    theme: 'dark' as const,
    language: 'en',
    window: {
      width: 1400,
      height: 900,
      minWidth: 800,
      minHeight: 600,
    },
  },
  logging: {
    level: 'info',
    format: 'json',
    backend_log: 'logs/backend.log',
    frontend_log: 'logs/frontend.log',
    max_size_mb: 50,
    backup_count: 5,
  },
  updates: {
    auto_check: true,
    channel: 'stable' as const,
    check_interval_hours: 24,
  },
  database: {
    type: 'sqlite',
    path: 'data/arkon.db',
  },
};

export const DEFAULT_PROVIDERS = {
  providers: [] as any[],
  routing_policy: 'auto',
  default_model: null as string | null,
};

export const DEFAULT_PLUGINS = {
  plugins: [] as any[],
  enabled: [] as string[],
  paths: ['plugins/'],
};

// --- Config Manager Class ---
export class ConfigManager {
  private dataDir: string | null = null;
  private configDir: string | null = null;
  private initialized = false;

  /**
   * Initialize the config manager with the app data directory.
   */
  async init(): Promise<void> {
    if (this.initialized) return;

    this.dataDir = await appDataDir();
    this.configDir = await join(this.dataDir, 'config');

    // Create directory structure
    await this.ensureDirectories();

    // Ensure default config files exist
    await this.ensureDefaults();

    this.initialized = true;
  }

  /**
   * Get the path to a config file.
   */
  private async getConfigPath(filename: string): Promise<string> {
    if (!this.configDir) throw new Error('ConfigManager not initialized');
    return await join(this.configDir, filename);
  }

  /**
   * Create the default directory structure.
   */
  private async ensureDirectories(): Promise<void> {
    if (!this.dataDir) throw new Error('ConfigManager not initialized');

    const dirs = [
      'config',
      'logs',
      'cache',
      'data',
      'workspace',
      'plugins',
      'exports',
    ];

    for (const dir of dirs) {
      const path = await join(this.dataDir, dir);
      if (!(await exists(path))) {
        await mkdir(path, { recursive: true });
      }
    }
  }

  /**
   * Ensure default config files exist.
   */
  private async ensureDefaults(): Promise<void> {
    const settingsPath = await this.getConfigPath('settings.json');
    if (!(await exists(settingsPath))) {
      await this.writeSettings(DEFAULT_SETTINGS);
    }

    const providersPath = await this.getConfigPath('providers.json');
    if (!(await exists(providersPath))) {
      await this.writeProviders(DEFAULT_PROVIDERS);
    }

    const pluginsPath = await this.getConfigPath('plugins.json');
    if (!(await exists(pluginsPath))) {
      await this.writePlugins(DEFAULT_PLUGINS);
    }
  }

  /**
   * Read the settings config file.
   */
  async readSettings(): Promise<typeof DEFAULT_SETTINGS> {
    const path = await this.getConfigPath('settings.json');
    const content = await readTextFile(path);
    return { ...DEFAULT_SETTINGS, ...JSON.parse(content) };
  }

  /**
   * Write the settings config file.
   */
  async writeSettings(settings: Partial<typeof DEFAULT_SETTINGS>): Promise<void> {
    const path = await this.getConfigPath('settings.json');
    const current = await this.readSettings();
    const merged = { ...current, ...settings };
    await writeTextFile(path, JSON.stringify(merged, null, 2));
  }

  /**
   * Read the providers config file.
   */
  async readProviders(): Promise<typeof DEFAULT_PROVIDERS> {
    const path = await this.getConfigPath('providers.json');
    const content = await readTextFile(path);
    return { ...DEFAULT_PROVIDERS, ...JSON.parse(content) };
  }

  /**
   * Write the providers config file.
   */
  async writeProviders(providers: Partial<typeof DEFAULT_PROVIDERS>): Promise<void> {
    const path = await this.getConfigPath('providers.json');
    const current = await this.readProviders();
    const merged = { ...current, ...providers };
    await writeTextFile(path, JSON.stringify(merged, null, 2));
  }

  /**
   * Read the plugins config file.
   */
  async readPlugins(): Promise<typeof DEFAULT_PLUGINS> {
    const path = await this.getConfigPath('plugins.json');
    const content = await readTextFile(path);
    return { ...DEFAULT_PLUGINS, ...JSON.parse(content) };
  }

  /**
   * Write the plugins config file.
   */
  async writePlugins(plugins: Partial<typeof DEFAULT_PLUGINS>): Promise<void> {
    const path = await this.getConfigPath('plugins.json');
    const current = await this.readPlugins();
    const merged = { ...current, ...plugins };
    await writeTextFile(path, JSON.stringify(merged, null, 2));
  }

  /**
   * Get the backend port from settings.
   */
  async getBackendPort(): Promise<number> {
    const settings = await this.readSettings();
    return settings.backend.port;
  }

  /**
   * Update the backend port in settings.
   */
  async setBackendPort(port: number): Promise<void> {
    const settings = await this.readSettings();
    settings.backend.port = port;
    await this.writeSettings(settings);
  }

  /**
   * Get the data directory path.
   */
  getDataDir(): string | null {
    return this.dataDir;
  }

  /**
   * Get the config directory path.
   */
  getConfigDir(): string | null {
    return this.configDir;
  }
}

// Singleton instance
export const configManager = new ConfigManager();
