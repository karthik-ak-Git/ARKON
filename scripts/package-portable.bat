@echo off
REM ============================================================
REM ARKON Portable Version Package
REM Creates a portable ZIP that can run without installation
REM ============================================================

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
set BACKEND_DIR=%PROJECT_ROOT%\backend
set DESKTOP_DIR=%PROJECT_ROOT%\apps\desktop
set TAURI_OUTPUT=%DESKTOP_DIR%\src-tauri\target\release\bundle
set RELEASE_DIR=%PROJECT_ROOT%\release
set PORTABLE_DIR=%RELEASE_DIR%\ARKON_Portable

echo.
echo ========================================
echo  ARKON Portable Package
echo ========================================
echo.

REM Clean previous portable build
if exist "%PORTABLE_DIR%" rmdir /s /q "%PORTABLE_DIR%"
if exist "%RELEASE_DIR%\ARKON_Portable.zip" del "%RELEASE_DIR%\ARKON_Portable.zip"
mkdir "%PORTABLE_DIR%"
mkdir "%RELEASE_DIR%"

REM Copy the built application
echo [1/6] Copying application files...
if exist "%TAURI_OUTPUT%\nsis\ARKON_*_x64-setup.exe" (
    copy "%TAURI_OUTPUT%\nsis\ARKON_*_x64-setup.exe" "%PORTABLE_DIR%\" >nul
) else if exist "%TAURI_OUTPUT%\msi\ARKON_*_x64.msi" (
    copy "%TAURI_OUTPUT%\msi\ARKON_*_x64.msi" "%PORTABLE_DIR%\" >nul
)

REM Copy the unpacked release directory
if exist "%DESKTOP_DIR%\src-tauri\target\release" (
    xcopy "%DESKTOP_DIR%\src-tauri\target\release\*.exe" "%PORTABLE_DIR%\" /Q /Y >nul 2>nul
)

REM Copy backend distribution
echo [2/6] Copying backend...
if exist "%BACKEND_DIR%\dist\backend" (
    xcopy "%BACKEND_DIR%\dist\backend" "%PORTABLE_DIR%\backend\" /E /I /Q /Y >nul
)

REM Copy Python runtime
echo [3/6] Copying Python runtime...
if exist "%BACKEND_DIR%\dist\python" (
    xcopy "%BACKEND_DIR%\dist\python" "%PORTABLE_DIR%\python\" /E /I /Q /Y >nul
)

REM Copy workers
echo [4/6] Copying workers...
if exist "%BACKEND_DIR%\dist\worker" (
    xcopy "%BACKEND_DIR%\dist\worker" "%PORTABLE_DIR%\worker\" /E /I /Q /Y >nul
)

REM Copy resources
echo [5/6] Copying resources...
if exist "%BACKEND_DIR%\dist\resources" (
    xcopy "%BACKEND_DIR%\dist\resources" "%PORTABLE_DIR%\resources\" /E /I /Q /Y >nul
)

REM Copy plugins
if exist "%BACKEND_DIR%\dist\plugins" (
    xcopy "%BACKEND_DIR%\dist\plugins" "%PORTABLE_DIR%\plugins\" /E /I /Q /Y >nul
)

REM Create launcher script
echo [6/6] Creating launcher...
(
echo @echo off
echo echo ========================================
echo echo  ARKON - AI Agent Operating Platform
echo echo ========================================
echo echo.
echo echo Starting ARKON...
echo.
echo REM Check if backend is already running
echo tasklist /FI "IMAGENAME eq backend.exe" 2^>nul ^| find /I "backend.exe" ^>nul
echo if %%errorlevel%% == 0 ^(
echo     echo Backend is already running.
echo ^) else ^(
echo     echo Starting backend...
echo     start /B "" "%%~dp0backend\backend.exe" --port 8000
echo     timeout /t 5 /nobreak ^>nul
echo     echo Backend started.
echo ^)
echo.
echo REM Launch the application
echo start "" "%%~dp0ARKON.exe"
echo.
echo echo ARKON is starting...
echo) > "%PORTABLE_DIR%\ARKON.bat"

REM Create README
(
echo ARKON - AI Agent Operating Platform
echo ====================================
echo.
echo Quick Start:
echo   1. Double-click ARON.bat to start the application
echo   2. The backend will start automatically
echo   3. The frontend will open in a window
echo.
echo Directory Structure:
echo   backend/   - Backend server
echo   python/    - Embedded Python runtime
echo   worker/    - Background job processor
echo   plugins/   - Plugin directory
echo   resources/ - Configuration templates
echo   logs/      - Application logs (created on first run)
echo   data/      - Application data (created on first run)
echo.
echo Configuration:
echo   Edit resources/settings.json to configure ARKON.
echo   Backend runs on http://localhost:8000 by default.
echo.
echo Troubleshooting:
echo   - If the app doesn't start, check logs/ directory
echo   - Ensure port 8000 is not in use
echo   - Run ARKON.bat as administrator if needed
echo) > "%PORTABLE_DIR%\README.txt"

REM Create ZIP
echo.
echo Creating portable ZIP...
cd "%RELEASE_DIR%"
powershell -Command "Compress-Archive -Path 'ARKON_Portable\*' -DestinationPath 'ARKON_Portable.zip' -Force"

echo.
echo ========================================
echo  Portable package created!
echo  Output: %RELEASE_DIR%\ARKON_Portable.zip
echo ========================================
echo.
