@echo off
REM ============================================================
REM ARKON Plugins Bundle
REM Packages plugin definitions for distribution
REM ============================================================

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
set BACKEND_DIR=%PROJECT_ROOT%\backend
set DIST_DIR=%BACKEND_DIR%\dist
set PLUGINS_DIR=%DIST_DIR%\plugins

echo.
echo [BUNDLE] Plugins
echo.

if not exist "%PLUGINS_DIR%" mkdir "%PLUGINS_DIR%"

REM Create plugin manifest
(
echo {
echo   "version": "1.0.0",
echo   "plugins": []
echo }
) > "%PLUGINS_DIR%\manifest.json"

REM Check for custom plugins
set PLUGIN_COUNT=0
for /d %%d in ("%PROJECT_ROOT%\plugins\*") do (
    set /a PLUGIN_COUNT+=1
    echo   Found plugin: %%~nxd
    xcopy "%%d" "%PLUGINS_DIR%\%%~nxd\" /E /I /Q /Y >nul
)

if %PLUGIN_COUNT%==0 (
    echo   No custom plugins found.
)

echo   Plugins bundled to: %PLUGINS_DIR%
echo.
