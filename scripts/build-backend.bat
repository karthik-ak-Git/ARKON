@echo off
REM ============================================================
REM ARKON Backend Build Script
REM Bundles Python backend into standalone executable using PyInstaller
REM ============================================================

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
set BACKEND_DIR=%PROJECT_ROOT%\backend
set WORKER_DIR=%PROJECT_ROOT%\worker
set DIST_DIR=%BACKEND_DIR%\dist
set BUILD_DIR=%BACKEND_DIR%\build

echo.
echo ========================================
echo  ARKON Backend Build
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.13.
    exit /b 1
)

REM Check PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous build
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%DIST_DIR%"
mkdir "%BUILD_DIR%"

echo.
echo [1/4] Installing backend dependencies...
cd "%BACKEND_DIR%"
pip install -e "." --quiet

echo.
echo [2/4] Building backend executable...
pyinstaller ^
    --name backend ^
    --distpath "%DIST_DIR%" ^
    --workpath "%BUILD_DIR%" ^
    --specpath "%BACKEND_DIR%" ^
    --onedir ^
    --console ^
    --hidden-import "app" ^
    --hidden-import "app.main" ^
    --hidden-import "app.core.config" ^
    --hidden-import "app.core.logging" ^
    --hidden-import "app.kernel.bootstrap" ^
    --hidden-import "app.kernel.kernel" ^
    --hidden-import "app.api" ^
    --hidden-import "app.api.health" ^
    --hidden-import "app.api.workspaces" ^
    --hidden-import "app.api.projects" ^
    --hidden-import "app.api.agents" ^
    --hidden-import "app.api.ai" ^
    --hidden-import "app.api.execution" ^
    --hidden-import "app.api.execution_ws" ^
    --hidden-import "app.api.runtime" ^
    --hidden-import "app.api.runtime_ws" ^
    --hidden-import "app.models" ^
    --hidden-import "app.models.domain" ^
    --hidden-import "app.models.workspace" ^
    --hidden-import "app.models.execution" ^
    --hidden-import "app.models.runtime" ^
    --hidden-import "app.database" ^
    --hidden-import "app.database.base" ^
    --hidden-import "app.database.engine" ^
    --hidden-import "app.database.session" ^
    --hidden-import "app.runtime" ^
    --hidden-import "app.execution" ^
    --hidden-import "app.ai" ^
    --hidden-import "app.workspace" ^
    --hidden-import "app.workflow" ^
    --hidden-import "app.capabilities" ^
    --hidden-import "app.events" ^
    --hidden-import "app.memory" ^
    --hidden-import "app.monitoring" ^
    --hidden-import "app.plugins" ^
    --hidden-import "app.orchestrator" ^
    --hidden-import "app.scheduler" ^
    --hidden-import "app.workers" ^
    --hidden-import "app.repositories" ^
    --hidden-import "app.services" ^
    --hidden-import "app.resources" ^
    --hidden-import "uvicorn" ^
    --hidden-import "uvicorn.logging" ^
    --hidden-import "uvicorn.loops" ^
    --hidden-import "uvicorn.loops.auto" ^
    --hidden-import "uvicorn.protocols" ^
    --hidden-import "uvicorn.protocols.http" ^
    --hidden-import "uvicorn.protocols.http.auto" ^
    --hidden-import "uvicorn.protocols.websockets" ^
    --hidden-import "uvicorn.protocols.websockets.auto" ^
    --hidden-import "uvicorn.lifespan" ^
    --hidden-import "uvicorn.lifespan.on" ^
    --hidden-import "fastapi" ^
    --hidden-import "pydantic" ^
    --hidden-import "pydantic_settings" ^
    --hidden-import "sqlalchemy" ^
    --hidden-import "sqlalchemy.ext.asyncio" ^
    --hidden-import "asyncpg" ^
    --hidden-import "structlog" ^
    --hidden-import "httpx" ^
    --hidden-import "nats" ^
    --hidden-import "redis" ^
    --collect-all "app" ^
    "%BACKEND_DIR%\app\main.py"

if errorlevel 1 (
    echo ERROR: Backend build failed!
    exit /b 1
)

echo.
echo [3/4] Building worker executable...
pyinstaller ^
    --name worker ^
    --distpath "%DIST_DIR%" ^
    --workpath "%BUILD_DIR%" ^
    --specpath "%BACKEND_DIR%" ^
    --onedir ^
    --console ^
    --hidden-import "worker" ^
    --hidden-import "worker.main" ^
    --hidden-import "app" ^
    --hidden-import "app.core.config" ^
    --hidden-import "app.core.logging" ^
    --hidden-import "app.database" ^
    --hidden-import "app.database.engine" ^
    --hidden-import "app.models.domain" ^
    --hidden-import "sqlalchemy" ^
    --hidden-import "sqlalchemy.ext.asyncio" ^
    --hidden-import "asyncpg" ^
    --hidden-import "structlog" ^
    "%WORKER_DIR%\main.py"

if errorlevel 1 (
    echo ERROR: Worker build failed!
    exit /b 1
)

echo.
echo [4/4] Cleaning up build artifacts...
rmdir /s /q "%BUILD_DIR%" 2>nul
rmdir /s /q "%BACKEND_DIR%\backend.spec" 2>nul
rmdir /s /q "%BACKEND_DIR%\worker.spec" 2>nul

echo.
echo ========================================
echo  Backend build complete!
echo  Output: %DIST_DIR%
echo ========================================
echo.

dir "%DIST_DIR%"
