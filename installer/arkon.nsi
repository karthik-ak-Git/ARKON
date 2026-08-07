; ============================================================
; ARKON NSIS Installer Script
; Creates a production Windows installer for ARKON
; ============================================================

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

; --- Installer Metadata ---
Name "ARKON"
OutFile "ARKON_Setup.exe"
InstallDir "$LOCALAPPDATA\ARKON"
InstallDirRegKey HKCU "Software\ARKON" "InstallDir"
RequestExecutionLevel admin
Unicode True

; --- Version Info ---
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "ARKON"
VIAddVersionKey "CompanyName" "ARKON"
VIAddVersionKey "FileDescription" "ARKON Installer"
VIAddVersionKey "FileVersion" "1.0.0"
VIAddVersionKey "ProductVersion" "1.0.0"

; --- MUI Settings ---
!define MUI_ABORTWARNING
!define MUI_ICON "src-tauri\icons\icon.ico"
!define MUI_UNICON "src-tauri\icons\icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "src-tauri\icons\installer-header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "src-tauri\icons\installer-sidebar.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "src-tauri\icons\installer-sidebar.bmp"

; --- Pages ---
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; --- Installer Init ---
Function .onInit
    ; Check if already installed
    IfFileExists "$INSTDIR\ARKON.exe" 0 +2
        MessageBox MB_YESNO|MB_ICONQUESTION "ARKON is already installed. Do you want to reinstall?" IDNO QuitInstaller
    Goto done
    QuitInstaller:
        Abort
    done:
FunctionEnd

; --- Sections ---
Section "ARKON (required)" SecMain
    SectionIn RO

    ; Set output path to install directory
    SetOutPath "$INSTDIR"

    ; Install main executable
    File "src-tauri\target\release\ARKON.exe"

    ; Install backend
    SetOutPath "$INSTDIR\backend"
    File /r "backend\dist\backend\*.*"

    ; Install Python runtime
    SetOutPath "$INSTDIR\python"
    File /r "backend\dist\python\*.*"

    ; Install workers
    SetOutPath "$INSTDIR\worker"
    File /r "backend\dist\worker\*.*"

    ; Install plugins
    SetOutPath "$INSTDIR\plugins"
    File /r "backend\dist\plugins\*.*"

    ; Install resources
    SetOutPath "$INSTDIR\resources"
    File /r "backend\dist\resources\*.*"

    ; Install Tauri runtime files
    SetOutPath "$INSTDIR"
    File "src-tauri\target\release\ARKON.exe"
    File /nonfatal "src-tauri\target\release\*.dll"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\ARKON"
    CreateShortCut "$SMPROGRAMS\ARKON\ARKON.lnk" "$INSTDIR\ARKON.exe"
    CreateShortCut "$SMPROGRAMS\ARKON\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

    ; Create Desktop shortcut
    CreateShortCut "$DESKTOP\ARKON.lnk" "$INSTDIR\ARKON.exe"

    ; Write registry keys
    WriteRegStr HKCU "Software\ARKON" "InstallDir" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ARKON" "DisplayName" "ARKON"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ARKON" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ARKON" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ARKON" "DisplayVersion" "1.0.0"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ARKON" "Publisher" "ARKON"
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ARKON" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ARKON" "NoRepair" 1

    ; Get installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ARKON" "EstimatedSize" "$0"
SectionEnd

Section "Post-Install"
    ; Create log directory
    CreateDirectory "$INSTDIR\logs"

    ; Create data directory
    CreateDirectory "$INSTDIR\data"

    ; Create cache directory
    CreateDirectory "$INSTDIR\cache"

    ; Create config directory
    CreateDirectory "$INSTDIR\config"

    ; Create workspace directory
    CreateDirectory "$INSTDIR\workspace"

    ; Copy default configuration files if they don't exist
    IfFileExists "$INSTDIR\config\settings.json" skip_settings
        CopyFiles "$INSTDIR\resources\settings.json.default" "$INSTDIR\config\settings.json"
    skip_settings:

    IfFileExists "$INSTDIR\config\providers.json" skip_providers
        CopyFiles "$INSTDIR\resources\providers.json.default" "$INSTDIR\config\providers.json"
    skip_providers:

    IfFileExists "$INSTDIR\config\plugins.json" skip_plugins
        CopyFiles "$INSTDIR\resources\plugins.json.default" "$INSTDIR\config\plugins.json"
    skip_plugins:

    ; Launch ARKON after installation
    MessageBox MB_YESNO|MB_ICONQUESTION "Installation complete! Do you want to launch ARKON now?" IDNO SkipLaunch
        Exec "$INSTDIR\ARKON.exe"
    SkipLaunch:
SectionEnd

; --- Uninstaller ---
Function un.onInit
    MessageBox MB_YESNO|MB_ICONQUESTION "Are you sure you want to uninstall ARKON?" IDNO AbortUninstall
    Goto done
    AbortUninstall:
        Abort
    done:
FunctionEnd

Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"

    ; Remove Start Menu shortcuts
    RMDir /r "$SMPROGRAMS\ARKON"

    ; Remove Desktop shortcut
    Delete "$DESKTOP\ARKON.lnk"

    ; Remove registry keys
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\ARKON"
    DeleteRegKey HKCU "Software\ARKON"
SectionEnd
