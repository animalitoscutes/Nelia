#!/usr/bin/env bash
# ==============================================================================
# NELIA Suite - Desktop Launcher & Auto-Setup (Linux / macOS)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "✨ =========================================="
echo "   NELIA — Suite de Escritura & Guion"
echo "=========================================="

# 1. Auto-create virtual environment and install dependencies if missing
if [ ! -d ".venv" ]; then
    echo "📦 Creando entorno virtual Python (.venv)..."
    python3 -m venv .venv
    echo "⬇️  Instalando dependencias desde requirements.txt..."
    .venv/bin/pip install --upgrade pip --quiet
    .venv/bin/pip install -r requirements.txt
fi

# 2. Check & spin up PostgreSQL via Docker if Docker is present
if command -v docker > /dev/null 2>&1 && docker info > /dev/null 2>&1; then
    echo "🐘 Iniciando base de datos PostgreSQL (Docker)..."
    docker compose up -d > /dev/null 2>&1 || true
    sleep 1
else
    echo "💡 [Info] Docker no está en ejecución. NELIA usará almacenamiento local SQLite automáticamente."
fi

# 3. Check Ollama (Local AI)
if command -v ollama > /dev/null 2>&1; then
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "🦙 Iniciando servicio Ollama en segundo plano..."
        ollama serve > /dev/null 2>&1 &
        sleep 1
    fi
else
    echo "💡 [Info] Ollama no detectado en el PATH. Las funciones de IA se activarán cuando instales Ollama."
fi

# 4. Launch Application
echo "🚀 Abriendo interfaz de NELIA..."
exec .venv/bin/python3 main.py "$@"
