@echo off
REM ARKON Portable Build Script
REM Creates a portable ZIP from the Tauri release build

setlocal

set DIST_DIR=%~dp0..\dist
set BUILD_DIR=%~dp0..\apps\desktop\src-tauri\target\release\bundle
set PORTABLE_DIR=%DIST_DIR%\ARKON-Portable

echo Creating portable build...

REM Clean previous portable build
if exist "%PORTABLE_DIR%" rmdir /s /q "%PORTABLE_DIR%"
mkdir "%PORTABLE_DIR%"

REM Copy the executable
copy "%BUILD_DIR%\nsis\arkon-desktop.exe" "%PORTABLE_DIR%\arkon-desktop.exe"

REM Create the ZIP
powershell -Command "Compress-Archive -Path '%PORTABLE_DIR%\*' -DestinationPath '%DIST_DIR%\ARKON-Portable.zip' -Force"

REM Generate checksum
powershell -Command "$hash = (Get-FileHash '%DIST_DIR%\ARKON-Portable.zip' -Algorithm SHA256).Hash.ToLower(); \"$hash  ARKON-Portable.zip\" | Out-File -FilePath '%DIST_DIR%\SHA256SUMS.txt' -Encoding utf8"

echo Portable build complete: %DIST_DIR%\ARKON-Portable.zip

endlocal
