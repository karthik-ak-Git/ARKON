@echo off
REM ============================================================
REM ARKON Workers Bundle
REM Packages background worker for distribution
REM ============================================================

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
set DIST_DIR=%PROJECT_ROOT%\backend\dist
set WORKERS_DIR=%DIST_DIR%\workers

echo.
echo [BUNDLE] Workers
echo.

if not exist "%WORKERS_DIR%" mkdir "%WORKERS_DIR%"

REM The worker executable should already be built by build-backend.bat
if exist "%DIST_DIR%\worker\worker.exe" (
    echo   Worker executable found.
) else (
    echo   WARNING: Worker executable not found at %DIST_DIR%\worker\worker.exe
    echo   Worker may need to be built separately.
)

REM Copy worker configuration
(
echo {
echo   "worker": {
echo     "enabled": true,
echo     "poll_interval_seconds": 5,
echo     "max_concurrent_jobs": 4,
echo     "retry_max_attempts": 3,
echo     "retry_delay_seconds": 10
echo   }
echo }
) > "%WORKERS_DIR%\worker.json.default"

echo   Workers bundled to: %WORKERS_DIR%
echo.
