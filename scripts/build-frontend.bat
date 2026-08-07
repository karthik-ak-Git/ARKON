@echo off
REM ============================================================
REM ARKON Frontend Build Script
REM Builds the React/Vite frontend for production
REM ============================================================

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
set DESKTOP_DIR=%PROJECT_ROOT%\apps\desktop

echo.
echo ========================================
echo  ARKON Frontend Build
echo ========================================
echo.

cd "%DESKTOP_DIR%"

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 20+.
    exit /b 1
)

echo [1/3] Installing frontend dependencies...
call npm install --production=false

echo.
echo [2/3] Type checking...
call npx tsc --noEmit
if errorlevel 1 (
    echo WARNING: Type check warnings found. Continuing build...
)

echo.
echo [3/3] Building frontend...
set DISABLE_HMR=true
call npx vite build

if errorlevel 1 (
    echo ERROR: Frontend build failed!
    exit /b 1
)

echo.
echo ========================================
echo  Frontend build complete!
echo  Output: %DESKTOP_DIR%\dist
echo ========================================
echo.
