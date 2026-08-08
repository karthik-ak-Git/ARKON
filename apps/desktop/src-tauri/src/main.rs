// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use arkon_lib::{BackendState, BackendStatus, HealthCheck};
use tauri::Emitter;
use tauri::Manager;
use tauri::State;
use tokio::process::Command;

// ── Backend Start Logic (non-Tauri, reusable) ─────────────────────

async fn do_start_backend(
    state: &BackendState,
    app_handle: &tauri::AppHandle,
) -> Result<BackendStatus, String> {
    let port = state.port;
    let pid = {
        let mut child_guard = state.child.lock().map_err(|e| e.to_string())?;

        if child_guard.is_some() {
            return Ok(BackendStatus {
                running: true,
                port,
                pid: child_guard.as_ref().and_then(|c| c.id()),
            });
        }

        let exe_path = arkon_lib::backend_exe_path(app_handle);
        let python_path = arkon_lib::python_runtime_path(app_handle);

        if !exe_path.exists() {
            return Err(format!(
                "Backend executable not found at: {}",
                exe_path.display()
            ));
        }

        let mut cmd = Command::new(&exe_path);
        cmd.arg("--port").arg(port.to_string());

        if python_path.exists() {
            cmd.env("PYTHONHOME", &python_path);
            cmd.env("PYTHONPATH", python_path.join("lib").join("python3.13"));
        }

        let data_dir = dirs::data_local_dir()
            .unwrap_or_else(|| std::path::PathBuf::from("."))
            .join("arkon");
        std::fs::create_dir_all(&data_dir).ok();
        cmd.env("STORAGE_PATH", data_dir.join("workspace"));
        cmd.env("DATABASE_URL", "sqlite+aiosqlite:///.arkon/arkon.db");

        let child = cmd
            .kill_on_drop(true)
            .spawn()
            .map_err(|e| format!("Failed to start backend: {}", e))?;

        let pid = child.id();
        *child_guard = Some(child);
        pid
    };

    log::info!("Backend started on port {}", port);

    Ok(BackendStatus {
        running: true,
        port,
        pid,
    })
}

// ── Tauri Commands ────────────────────────────────────────────────

#[tauri::command]
async fn start_backend(
    state: State<'_, BackendState>,
    app_handle: tauri::AppHandle,
) -> Result<BackendStatus, String> {
    do_start_backend(&state, &app_handle).await
}

#[tauri::command]
async fn stop_backend(state: State<'_, BackendState>) -> Result<BackendStatus, String> {
    let port = state.port;
    let child_opt = {
        let mut child_guard = state.child.lock().map_err(|e| e.to_string())?;
        child_guard.take()
    };

    if let Some(mut child) = child_opt {
        child
            .kill()
            .await
            .map_err(|e| format!("Failed to stop backend: {}", e))?;
        log::info!("Backend stopped");
    }

    Ok(BackendStatus {
        running: false,
        port,
        pid: None,
    })
}

#[tauri::command]
async fn get_backend_status(state: State<'_, BackendState>) -> Result<BackendStatus, String> {
    let child_guard = state.child.lock().map_err(|e| e.to_string())?;

    Ok(BackendStatus {
        running: child_guard.is_some(),
        port: state.port,
        pid: child_guard.as_ref().and_then(|c| c.id()),
    })
}

#[tauri::command]
async fn check_backend_health(state: State<'_, BackendState>) -> Result<HealthCheck, String> {
    let url = format!("http://127.0.0.1:{}/health", state.port);

    match reqwest::get(&url).await {
        Ok(resp) => {
            if resp.status().is_success() {
                Ok(HealthCheck {
                    healthy: true,
                    message: "Backend is healthy".to_string(),
                })
            } else {
                Ok(HealthCheck {
                    healthy: false,
                    message: format!("Backend returned status: {}", resp.status()),
                })
            }
        }
        Err(e) => Ok(HealthCheck {
            healthy: false,
            message: format!("Cannot reach backend: {}", e),
        }),
    }
}

#[tauri::command]
fn get_backend_port(state: State<'_, BackendState>) -> u16 {
    state.port
}

#[tauri::command]
async fn auto_start_backend(
    state: State<'_, BackendState>,
    app_handle: tauri::AppHandle,
) -> Result<BackendStatus, String> {
    let port = state.port;
    let already_running = {
        let guard = state.child.lock().map_err(|e| e.to_string())?;
        guard.is_some()
    };

    if !already_running {
        start_backend(state.clone(), app_handle).await?;
    }

    let healthy = arkon_lib::wait_for_backend(port, 30).await;
    if !healthy {
        return Err("Backend failed to start within 30 seconds".to_string());
    }

    let guard = state.child.lock().map_err(|e| e.to_string())?;
    Ok(BackendStatus {
        running: true,
        port,
        pid: guard.as_ref().and_then(|c| c.id()),
    })
}

// ── Entry Point ───────────────────────────────────────────────────

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_os::init())
        .manage(arkon_lib::create_backend_state(8000))
        .setup(|app| {
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

            // ── Auto-start backend + crash watcher ─────────────────
            let handle = app.handle().clone();
            let port = {
                let state = handle.state::<BackendState>();
                state.port
            };

            tauri::async_runtime::spawn({
                let handle = handle.clone();
                async move {
                    // Emit: starting
                    let _ = handle.emit("backend:status", serde_json::json!({
                        "status": "starting",
                        "port": port,
                        "pid": null,
                    }));

                    // Start backend
                    let state_ref = handle.state::<BackendState>();
                    match do_start_backend(&state_ref, &handle).await {
                        Ok(status) => {
                            // Wait for health
                            let healthy = arkon_lib::wait_for_backend(port, 30).await;
                            if healthy {
                                log::info!("Backend healthy on port {}", port);
                                let _ = handle.emit("backend:status", serde_json::json!({
                                    "status": "healthy",
                                    "port": port,
                                    "pid": status.pid,
                                }));
                            } else {
                                log::warn!("Backend started but health check failed after 30s");
                                let _ = handle.emit("backend:status", serde_json::json!({
                                    "status": "error",
                                    "port": port,
                                    "pid": null,
                                    "message": "Backend started but health check failed",
                                }));
                            }
                        }
                        Err(e) => {
                            log::error!("Failed to start backend: {}", e);
                            let _ = handle.emit("backend:status", serde_json::json!({
                                "status": "error",
                                "port": port,
                                "pid": null,
                                "message": e,
                            }));
                            return;
                        }
                    }
                    drop(state_ref);

                    // Crash watcher — poll health, auto-restart on failure
                    loop {
                        tokio::time::sleep(tokio::time::Duration::from_secs(10)).await;

                        let is_running = {
                            let state_ref = handle.state::<BackendState>();
                            let guard = state_ref.child.lock().unwrap_or_else(|e| e.into_inner());
                            guard.is_some()
                        };

                        if !is_running {
                            log::warn!("Backend process gone, restarting...");
                            let _ = handle.emit("backend:status", serde_json::json!({
                                "status": "restarting",
                                "port": port,
                                "pid": null,
                            }));

                            let state_ref = handle.state::<BackendState>();
                            match do_start_backend(&state_ref, &handle).await {
                                Ok(status) => {
                                    let healthy = arkon_lib::wait_for_backend(port, 30).await;
                                    if healthy {
                                        log::info!("Backend restarted and healthy");
                                        let _ = handle.emit("backend:status", serde_json::json!({
                                            "status": "healthy",
                                            "port": port,
                                            "pid": status.pid,
                                        }));
                                    } else {
                                        let _ = handle.emit("backend:status", serde_json::json!({
                                            "status": "error",
                                            "port": port,
                                            "pid": null,
                                            "message": "Restart failed health check",
                                        }));
                                    }
                                }
                                Err(e) => {
                                    log::error!("Failed to restart backend: {}", e);
                                    let _ = handle.emit("backend:status", serde_json::json!({
                                        "status": "error",
                                        "port": port,
                                        "pid": null,
                                        "message": e,
                                    }));
                                }
                            }
                        }
                    }
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            start_backend,
            stop_backend,
            get_backend_status,
            check_backend_health,
            get_backend_port,
            auto_start_backend,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let tauri::RunEvent::ExitRequested { .. } = event {
                let state: State<BackendState> = app_handle.state();
                // Drop child — kill_on_drop(true) handles the kill
                let mut guard = state.child.lock().unwrap_or_else(|e| e.into_inner());
                if guard.take().is_some() {
                    log::info!("Shutting down backend gracefully...");
                }
            }
        });
}
