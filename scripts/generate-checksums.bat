@echo off
REM ARKON SHA256 Checksum Generator
REM Generates SHA256SUMS.txt for all release artifacts

setlocal

set DIST_DIR=%~dp0..\dist
set OUTPUT=%DIST_DIR%\SHA256SUMS.txt

echo Generating SHA256 checksums...

if exist "%OUTPUT%" del "%OUTPUT%"

REM Check for artifacts
if exist "%DIST_DIR%\ARKON-Portable.zip" (
    powershell -Command "$hash = (Get-FileHash '%DIST_DIR%\ARKON-Portable.zip' -Algorithm SHA256).Hash.ToLower(); \"$hash  ARKON-Portable.zip\" | Out-File -FilePath '%OUTPUT%' -Encoding utf8"
)

REM Also check for NSIS installer
set NSIS_DIR=%~dp0..\apps\desktop\src-tauri\target\release\bundle\nsis
if exist "%NSIS_DIR%\*.exe" (
    powershell -Command "Get-ChildItem '%NSIS_DIR%\*.exe' | ForEach-Object { $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(); \"$hash  $($_.Name)\" } | Out-File -FilePath '%OUTPUT%' -Encoding utf8 -Append"
)

echo Checksums written to: %OUTPUT%

endlocal
