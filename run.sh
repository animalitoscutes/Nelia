#!/usr/bin/env bash
# ==============================================================================
# NELIA Suite - Desktop Launcher & Auto-Setup (Linux / macOS)
# Double-click or run from terminal without extra setup.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "✨ =========================================="
echo "   NELIA — Suite de Escritura & Guion"
echo "=========================================="
echo ""

# Detect python command
PYTHON_BIN=""
if command -v python3 > /dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python > /dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "❌ [Error] No se encontró Python en el sistema."
    echo "Por favor instala Python 3.10 o superior (ej: sudo apt install python3 python3-venv python3-pip)."
    read -p "Presiona Enter para salir..."
    exit 1
fi

# 1. Auto-create virtual environment and install dependencies on first run
if [ ! -f ".venv/bin/python3" ]; then
    echo "📦 [1/3] Configurando entorno virtual (.venv) por primera vez..."
    $PYTHON_BIN -m venv .venv || {
        echo "⚠️  [Aviso] Si estás en Ubuntu/Debian, ejecuta: sudo apt install python3-venv"
        read -p "Presiona Enter para salir..."
        exit 1
    }
    echo "⬇️  [2/3] Instalando dependencias de requirements.txt..."
    .venv/bin/pip install --upgrade pip --quiet
    .venv/bin/pip install -r requirements.txt
    echo "✅ [OK] Instalación completada."
fi

# 2. Check & spin up PostgreSQL via Docker if Docker is present
if command -v docker > /dev/null 2>&1 && docker info > /dev/null 2>&1; then
    docker compose up -d > /dev/null 2>&1 || true
fi

# 3. Check Ollama (Local AI)
if command -v ollama > /dev/null 2>&1; then
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "🦙 Iniciando servicio Ollama en segundo plano..."
        ollama serve > /dev/null 2>&1 &
        sleep 1
    fi
fi

# 4. Launch Application
echo "🚀 [3/3] Abriendo NELIA..."
exec .venv/bin/python3 main.py "$@"
