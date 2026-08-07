// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use arkon_lib::BackendState;
use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_os::init())
        .manage(arkon_lib::create_backend_state(8000))
        .setup(|app| {
            // Setup directories on first launch
            let app_data_dir = app
                .path()
                .app_data_dir()
                .expect("Failed to get app data dir");

            std::fs::create_dir_all(app_data_dir.join("config"))
                .expect("Failed to create config dir");
            std::fs::create_dir_all(app_data_dir.join("logs"))
                .expect("Failed to create logs dir");
            std::fs::create_dir_all(app_data_dir.join("cache"))
                .expect("Failed to create cache dir");
            std::fs::create_dir_all(app_data_dir.join("data"))
                .expect("Failed to create data dir");
            std::fs::create_dir_all(app_data_dir.join("workspace"))
                .expect("Failed to create workspace dir");
            std::fs::create_dir_all(app_data_dir.join("plugins"))
                .expect("Failed to create plugins dir");
            std::fs::create_dir_all(app_data_dir.join("exports"))
                .expect("Failed to create exports dir");

            // Write default config files if they don't exist
            let config_dir = app_data_dir.join("config");

            if !config_dir.join("settings.json").exists() {
                let default_settings = serde_json::json!({
                    "version": "1.0.0",
                    "backend": {
                        "port": 8000,
                        "host": "127.0.0.1",
                        "auto_start": true,
                        "auto_restart": true,
                        "log_level": "info"
                    },
                    "frontend": {
                        "theme": "dark",
                        "language": "en",
                        "window": {
                            "width": 1400,
                            "height": 900,
                            "minWidth": 800,
                            "minHeight": 600
                        }
                    },
                    "logging": {
                        "level": "info",
                        "format": "json",
                        "backend_log": "logs/backend.log",
                        "frontend_log": "logs/frontend.log",
                        "max_size_mb": 50,
                        "backup_count": 5
                    },
                    "updates": {
                        "auto_check": true,
                        "channel": "stable",
                        "check_interval_hours": 24
                    },
                    "database": {
                        "type": "sqlite",
                        "path": "data/arkon.db"
                    }
                });

                std::fs::write(
                    config_dir.join("settings.json"),
                    serde_json::to_string_pretty(&default_settings)
                        .expect("Failed to serialize settings"),
                )
                .expect("Failed to write settings.json");
            }

            if !config_dir.join("providers.json").exists() {
                let default_providers = serde_json::json!({
                    "providers": [],
                    "routing_policy": "auto",
                    "default_model": null
                });

                std::fs::write(
                    config_dir.join("providers.json"),
                    serde_json::to_string_pretty(&default_providers)
                        .expect("Failed to serialize providers"),
                )
                .expect("Failed to write providers.json");
            }

            if !config_dir.join("plugins.json").exists() {
                let default_plugins = serde_json::json!({
                    "plugins": [],
                    "enabled": [],
                    "paths": ["plugins/"]
                });

                std::fs::write(
                    config_dir.join("plugins.json"),
                    serde_json::to_string_pretty(&default_plugins)
                        .expect("Failed to serialize plugins"),
                )
                .expect("Failed to write plugins.json");
            }

            // Get app handle for monitoring
            let handle = app.handle().clone();
            let state: tauri::State<BackendState> = handle.state();

            // Start backend monitoring in background
            let monitor_state = BackendState {
                child: std::sync::Mutex::new(None),
                port: state.port,
                shutdown_tx: state.shutdown_tx.clone(),
            };

            tauri::async_runtime::spawn(async move {
                // Auto-start backend
                log::info!("Auto-starting backend...");
                match arkon_lib::auto_start_backend(
                    tauri::State::new(&monitor_state),
                    handle.clone(),
                )
                .await
                {
                    Ok(status) => {
                        log::info!("Backend started: {:?}", status);
                        // Move the child to the managed state
                        // (In production, this would be done differently)
                    }
                    Err(e) => {
                        log::error!("Failed to auto-start backend: {}", e);
                    }
                }

                // Start monitoring
                arkon_lib::monitor_backend(&monitor_state, handle).await;
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            arkon_lib::start_backend,
            arkon_lib::stop_backend,
            arkon_lib::get_backend_status,
            arkon_lib::check_backend_health,
            arkon_lib::get_backend_port,
            arkon_lib::auto_start_backend,
        ])
        .on_event(|app_handle, event| {
            if let tauri::Event::ExitRequested { .. } = event {
                // Graceful shutdown
                let state: tauri::State<BackendState> = app_handle.state();
                tauri::async_runtime::block_on(async {
                    arkon_lib::shutdown_backend(&state).await;
                });
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
