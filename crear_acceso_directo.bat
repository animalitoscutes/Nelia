@echo off
REM ==============================================================================
REM NELIA - Creador de Acceso Directo de Escritorio (Windows)
REM ==============================================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

set TARGET_BAT=%~dp0run.bat
set ICON_PATH=%~dp0assets\icon.ico
set SHORTCUT_PATH=%USERPROFILE%\Desktop\NELIA.lnk

echo Creando acceso directo en el Escritorio...

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%TARGET_BAT%'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = '%ICON_PATH%'; $s.Description = 'NELIA - Suite de Escritura y Guion'; $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo [EXITO] Acceso directo 'NELIA' creado en tu Escritorio con el icono oficial.
) else (
    echo [AVISO] No se pudo crear el acceso directo automaticamente.
)

pause
