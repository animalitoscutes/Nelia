@echo off
REM ==============================================================================
REM NELIA Suite - Desktop Launcher & Auto-Setup (Windows)
REM Double-click to run without terminal commands.
REM ==============================================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"
title NELIA — Suite de Escritura ^& Guion

echo ===================================================
echo        NELIA — Suite de Escritura ^& Guion
echo ===================================================
echo.

REM Detect Python executable (python or py)
set PYTHON_CMD=
where python >nul 2>&1 && set PYTHON_CMD=python
if not defined PYTHON_CMD (
    where py >nul 2>&1 && set PYTHON_CMD=py
)

if not defined PYTHON_CMD (
    echo [ERROR] No se encontro Python en el sistema.
    echo Por favor descarga e instala Python 3.10+ desde https://www.python.org/
    echo Recuerda marcar la casilla "Add python.exe to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

REM 1. Auto-create virtual environment and install dependencies on first run
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Configurando entorno por primera vez...
    %PYTHON_CMD% -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo [2/3] Instalando librerias necesarias (esto solo toma un minuto)...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt
    echo [OK] Instalacion completada con exito.
) else (
    call .venv\Scripts\activate.bat
)

REM 2. Intentar levantar PostgreSQL si Docker esta instalado y corriendo
docker compose up -d >nul 2>&1
if %errorlevel% neq 0 (
    echo [Info] Docker inactivo o no instalado. Usando almacenamiento local SQLite.
)

REM 3. Iniciar aplicacion
echo [3/3] Abriendo NELIA...
python main.py %*
if %errorlevel% neq 0 (
    echo.
    echo [Aviso] La aplicacion se cerro. Si hubo algun problema revisa los mensajes arriba.
    pause
)
