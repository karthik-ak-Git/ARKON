@echo off
REM ============================================================
REM ARKON Resources Bundle
REM Copies static resources into the distribution
REM ============================================================

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
set BACKEND_DIR=%PROJECT_ROOT%\backend
set DIST_DIR=%BACKEND_DIR%\dist
set RESOURCES_DIR=%DIST_DIR%\resources

echo.
echo [BUNDLE] Resources
echo.

if not exist "%RESOURCES_DIR%" mkdir "%RESOURCES_DIR%"

REM Create default configuration templates
echo   Creating default configuration...

(
echo {
echo   "version": "1.0.0",
echo   "backend": {
echo     "port": 8000,
echo     "host": "127.0.0.1",
echo     "auto_start": true,
echo     "auto_restart": true,
echo     "log_level": "info"
echo   },
echo   "frontend": {
echo     "theme": "dark",
echo     "language": "en",
echo     "window": {
echo       "width": 1400,
echo       "height": 900,
echo       "minWidth": 800,
echo       "minHeight": 600
echo     }
echo   },
echo   "logging": {
echo     "level": "info",
echo     "format": "json",
echo     "backend_log": "logs/backend.log",
echo     "frontend_log": "logs/frontend.log",
echo     "worker_log": "logs/worker.log",
echo     "max_size_mb": 50,
echo     "backup_count": 5
echo   },
echo   "updates": {
echo     "auto_check": true,
echo     "channel": "stable",
echo     "check_interval_hours": 24
echo   },
echo   "database": {
echo     "type": "sqlite",
echo     "path": "data/arkon.db"
echo   }
echo }
) > "%RESOURCES_DIR%\settings.json.default"

(
echo {
echo   "providers": [],
echo   "routing_policy": "auto",
echo   "default_model": null
echo }
) > "%RESOURCES_DIR%\providers.json.default"

(
echo {
echo   "plugins": [],
echo   "enabled": [],
echo   "paths": ["plugins/"]
echo }
) > "%RESOURCES_DIR%\plugins.json.default"

REM Copy workspace template
if not exist "%RESOURCES_DIR%\workspace" mkdir "%RESOURCES_DIR%\workspace"
if not exist "%RESOURCES_DIR%\workspace\.gitkeep" type nul > "%RESOURCES_DIR%\workspace\.gitkeep"

REM Copy any existing plugin definitions
if exist "%PROJECT_ROOT%\plugins\*" (
    xcopy "%PROJECT_ROOT%\plugins\*" "%RESOURCES_DIR%\plugins\" /E /I /Q /Y >nul
    echo   Plugins copied.
)

echo   Resources bundled to: %RESOURCES_DIR%
echo.
