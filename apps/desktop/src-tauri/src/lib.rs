use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use tauri::Manager;
use tokio::process::Child;
use tokio::sync::watch;
use tokio::time::{sleep, Duration};

/// Backend process manager state
pub struct BackendState {
    pub child: Mutex<Option<Child>>,
    pub port: u16,
    pub shutdown_tx: watch::Sender<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackendStatus {
    pub running: bool,
    pub port: u16,
    pub pid: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthCheck {
    pub healthy: bool,
    pub message: String,
}

/// Get the path to the bundled backend executable
pub fn backend_exe_path(app_handle: &tauri::AppHandle) -> std::path::PathBuf {
    let resource_dir = app_handle
        .path()
        .resource_dir()
        .expect("Failed to resolve resource directory");

    let dev_path = std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../backend/dist/backend.exe");

    if dev_path.exists() {
        return dev_path;
    }

    resource_dir.join("backend").join("backend.exe")
}

/// Get the path to the Python runtime directory
pub fn python_runtime_path(app_handle: &tauri::AppHandle) -> std::path::PathBuf {
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

/// Create BackendState with given port
pub fn create_backend_state(port: u16) -> BackendState {
    let (shutdown_tx, _) = watch::channel(false);
    BackendState {
        child: Mutex::new(None),
        port,
        shutdown_tx,
    }
}
