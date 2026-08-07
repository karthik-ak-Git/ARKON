@echo off
REM ============================================================
REM ARKON Python Runtime Bundle
REM Copies Python runtime files needed by the bundled backend
REM ============================================================

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
set BACKEND_DIR=%PROJECT_ROOT%\backend
set DIST_DIR=%BACKEND_DIR%\dist
set PYTHON_RUNTIME_DIR=%DIST_DIR%\python

echo.
echo [BUNDLE] Python Runtime
echo.

REM Create python runtime directory
if not exist "%PYTHON_RUNTIME_DIR%" mkdir "%PYTHON_RUNTIME_DIR%"
if not exist "%PYTHON_RUNTIME_DIR%\lib" mkdir "%PYTHON_RUNTIME_DIR%\lib"

REM Copy Python standard library
echo   Copying Python standard library...
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.prefix)"') do set PYTHON_PREFIX=%%i
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.version[:4])"') do set PYTHON_VERSION=%%i

REM Copy Lib directory (standard library)
if exist "%PYTHON_PREFIX%\Lib" (
    xcopy "%PYTHON_PREFIX%\Lib" "%PYTHON_RUNTIME_DIR%\Lib\" /E /I /Q /Y >nul
    echo   Standard library copied.
) else (
    echo   WARNING: Python Lib directory not found at %PYTHON_PREFIX%\Lib
)

REM Copy DLLs
if exist "%PYTHON_PREFIX%\python*.dll" (
    copy "%PYTHON_PREFIX%\python*.dll" "%PYTHON_RUNTIME_DIR%\" >nul
    echo   Python DLLs copied.
)

REM Copy python3.dll
if exist "%PYTHON_PREFIX%\python3.dll" (
    copy "%PYTHON_PREFIX%\python3.dll" "%PYTHON_RUNTIME_DIR%\" >nul
)

REM Copy python313.dll specifically
if exist "%PYTHON_PREFIX%\python313.dll" (
    copy "%PYTHON_PREFIX%\python313.dll" "%PYTHON_RUNTIME_DIR%\" >nul
)

REM Copy vcruntime140.dll if present
if exist "%PYTHON_PREFIX%\vcruntime140.dll" (
    copy "%PYTHON_PREFIX%\vcruntime140.dll" "%PYTHON_RUNTIME_DIR%\" >nul
)

REM Create a site-packages directory for dependencies
if not exist "%PYTHON_RUNTIME_DIR%\Lib\site-packages" mkdir "%PYTHON_RUNTIME_DIR%\Lib\site-packages"

REM Copy installed packages
echo   Copying installed packages...
pip freeze > "%TEMP%\arkon_packages.txt"

REM Copy key packages needed by the backend
for %%p in (
    fastapi
    uvicorn
    sqlalchemy
    pydantic
    pydantic_settings
    structlog
    httpx
    nats
    redis
    asyncpg
    starlette
    anyio
    idna
    sniffio
    certifi
    urllib3
    h11
    click
    markdown_it
    pygments
    rich
    greenlet
    aiofiles
    python_multipart
    jinja2
    itsdangerous
    typing_extensions
    annotated_types
) do (
    pip show %%p >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2 delims=: " %%a in ('pip show %%p ^| findstr "Location:"') do (
            set PKG_LOCATION=%%a
        )
        if defined PKG_LOCATION (
            xcopy "!PKG_LOCATION!\%%p" "%PYTHON_RUNTIME_DIR%\Lib\site-packages\%%p\" /E /I /Q /Y >nul 2>nul
        )
    )
)

echo.
echo   Python runtime bundled to: %PYTHON_RUNTIME_DIR%
echo.
