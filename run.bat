@echo off
REM ==============================================================================
REM NELIA Suite - Desktop Launcher & Auto-Setup (Windows)
REM ==============================================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ==========================================
echo    NELIA — Suite de Escritura ^& Guion
echo ==========================================

REM 1. Auto-create virtual environment and install dependencies if missing
if not exist ".venv" (
    echo [NELIA] Creando entorno virtual Python (.venv)...
    python -m venv .venv
    echo [NELIA] Instalando dependencias desde requirements.txt...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

REM 2. Try starting Docker Compose if docker is running
docker compose up -d >nul 2>&1
if %errorlevel% neq 0 (
    echo [NELIA] Docker no detectado o inactivo. NELIA usara SQLite local automaticamente.
)

REM 3. Launch Application
echo [NELIA] Abriendo interfaz de NELIA...
python main.py %*
pause
