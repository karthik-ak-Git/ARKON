use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use tauri::State;
use tokio::process::{Child, Command};
use tokio::sync::watch;
use tokio::time::{sleep, Duration};

/// Backend process manager state
pub struct BackendState {
    child: Mutex<Option<Child>>,
    port: u16,
    shutdown_tx: watch::Sender<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BackendStatus {
    pub running: bool,
    pub port: u16,
    pub pid: Option<u32>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthCheck {
    pub healthy: bool,
    pub message: String,
}

/// Get the path to the bundled backend executable
fn backend_exe_path(app_handle: &tauri::AppHandle) -> std::path::PathBuf {
    let resource_dir = app_handle
        .path()
        .resource_dir()
        .expect("Failed to resolve resource directory");

    // In dev mode, look in ../../backend/dist/
    // In production, look in the resource directory
    let dev_path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../backend/dist/backend.exe");

    if dev_path.exists() {
        return dev_path;
    }

    resource_dir.join("backend").join("backend.exe")
}

/// Get the path to the Python runtime directory
fn python_runtime_path(app_handle: &tauri::AppHandle) -> std::path::PathBuf {
    let resource_dir = app_handle
        .path()
        .resource_dir()
        .expect("Failed to resolve resource directory");

    let dev_path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../backend/dist/python");

    if dev_path.exists() {
        return dev_path;
    }

    resource_dir.join("backend").join("python")
}

/// Start the backend process
#[tauri::command]
pub async fn start_backend(
    state: State<'_, BackendState>,
    app_handle: tauri::AppHandle,
) -> Result<BackendStatus, String> {
    let mut child_guard = state.child.lock().map_err(|e| e.to_string())?;

    if child_guard.is_some() {
        return Ok(BackendStatus {
            running: true,
            port: state.port,
            pid: child_guard.as_ref().and_then(|c| c.id()),
        });
    }

    let exe_path = backend_exe_path(&app_handle);
    let python_path = python_runtime_path(&app_handle);

    if !exe_path.exists() {
        return Err(format!("Backend executable not found at: {}", exe_path.display()));
    }

    // Set up environment for the backend
    let mut cmd = Command::new(&exe_path);
    cmd.arg("--port").arg(state.port.to_string());

    // If Python runtime is bundled, set PYTHONHOME
    if python_path.exists() {
        cmd.env("PYTHONHOME", &python_path);
        cmd.env("PYTHONPATH", python_path.join("lib").join("python3.13"));
    }

    // Set storage path to user data directory
    let data_dir = dirs::data_local_dir()
        .unwrap_or_else(|| std::path::PathBuf::from("."))
        .join("arkon");
    std::fs::create_dir_all(&data_dir).ok();
    cmd.env("STORAGE_PATH", data_dir.join("workspace"));
    cmd.env("DATABASE_URL", "sqlite+aiosqlite:///.arkon/arkon.db");

    // Spawn the process
    let child = cmd
        .kill_on_drop(true)
        .spawn()
        .map_err(|e| format!("Failed to start backend: {}", e))?;

    *child_guard = Some(child);

    log::info!("Backend started on port {}", state.port);

    Ok(BackendStatus {
        running: true,
        port: state.port,
        pid: child_guard.as_ref().and_then(|c| c.id()),
    })
}

/// Stop the backend process
#[tauri::command]
pub async fn stop_backend(state: State<'_, BackendState>) -> Result<BackendStatus, String> {
    let mut child_guard = state.child.lock().map_err(|e| e.to_string())?;

    if let Some(ref mut child) = *child_guard {
        child.kill().await.map_err(|e| format!("Failed to stop backend: {}", e))?;
        *child_guard = None;
        log::info!("Backend stopped");
    }

    Ok(BackendStatus {
        running: false,
        port: state.port,
        pid: None,
    })
}

/// Get backend status
#[tauri::command]
pub async fn get_backend_status(state: State<'_, BackendState>) -> Result<BackendStatus, String> {
    let child_guard = state.child.lock().map_err(|e| e.to_string())?;

    let running = child_guard.is_some();
    let pid = child_guard.as_ref().and_then(|c| c.id());

    Ok(BackendStatus {
        running,
        port: state.port,
        pid,
    })
}

/// Check backend health via HTTP
#[tauri::command]
pub async fn check_backend_health(state: State<'_, BackendState>) -> Result<HealthCheck, String> {
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

/// Wait for backend to become healthy (with timeout)
pub async fn wait_for_backend(port: u16, timeout_secs: u64) -> bool {
    let url = format!("http://127.0.0.1:{}/health", port);
    let start = std::time::Instant::now();
    let timeout = Duration::from_secs(timeout_secs);

    loop {
        if start.elapsed() > timeout {
            return false;
        }

        match reqwest::get(&url).await {
            Ok(resp) if resp.status().is_success() => return true,
            _ => sleep(Duration::from_millis(500)).await,
        }
    }
}

/// Get the backend port (for frontend configuration)
#[tauri::command]
pub fn get_backend_port(state: State<'_, BackendState>) -> u16 {
    state.port
}

/// Auto-start backend and wait for health
#[tauri::command]
pub async fn auto_start_backend(
    state: State<'_, BackendState>,
    app_handle: tauri::AppHandle,
) -> Result<BackendStatus, String> {
    // Start if not running
    let status = {
        let guard = state.child.lock().map_err(|e| e.to_string())?;
        guard.is_some()
    };

    if !status {
        start_backend(state, app_handle).await?;
    }

    // Wait for health
    let healthy = wait_for_backend(state.port, 30).await;
    if !healthy {
        return Err("Backend failed to start within 30 seconds".to_string());
    }

    Ok(BackendStatus {
        running: true,
        port: state.port,
        pid: {
            let guard = state.child.lock().map_err(|e| e.to_string())?;
            guard.as_ref().and_then(|c| c.id())
        },
    })
}

/// Monitor backend and restart if it crashes
pub async fn monitor_backend(state: &BackendState, app_handle: tauri::AppHandle) {
    loop {
        sleep(Duration::from_secs(5)).await;

        let should_restart = {
            let mut guard = state.child.lock().unwrap_or_else(|e| e.into_inner());
            if let Some(ref mut child) = *guard {
                // Check if process is still running
                match child.try_wait() {
                    Ok(Some(status)) => {
                        log::warn!("Backend process exited with: {}", status);
                        *guard = None;
                        true
                    }
                    Ok(None) => false,
                    Err(e) => {
                        log::error!("Error checking backend: {}", e);
                        *guard = None;
                        true
                    }
                }
            } else {
                false
            }
        };

        if should_restart {
            log::info!("Auto-restarting backend...");
            let _ = start_backend(State::new(state), app_handle.clone()).await;
            let healthy = wait_for_backend(state.port, 30).await;
            if healthy {
                log::info!("Backend restarted successfully");
            } else {
                log::error!("Backend failed to restart");
            }
        }
    }
}

/// Graceful shutdown
pub async fn shutdown_backend(state: &BackendState) {
    let mut guard = state.child.lock().unwrap_or_else(|e| e.into_inner());
    if let Some(ref mut child) = *guard {
        log::info!("Shutting down backend gracefully...");
        // Send SIGTERM equivalent (on Windows, just kill)
        let _ = child.kill().await;
        *guard = None;
    }
}

/// Create BackendState with given port
pub fn create_backend_state(port: u16) -> BackendState {
    let (shutdown_tx, _) = watch::channel(false);
    BackendState {
        child: Mutex::new(None),
        port,
        shutdown_tx,
    }
}
