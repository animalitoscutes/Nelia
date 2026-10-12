#!/usr/bin/env bash
# ==============================================================================
# NELIA - Creador de Acceso Directo de Escritorio y Menú del Sistema (Linux)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DESKTOP_DIR=""
if [ -d "$HOME/Escritorio" ]; then
    DESKTOP_DIR="$HOME/Escritorio"
elif [ -d "$HOME/Desktop" ]; then
    DESKTOP_DIR="$HOME/Desktop"
fi

DESKTOP_ENTRY="[Desktop Entry]
Version=1.0
Type=Application
Name=NELIA
Comment=Suite de Escritura Creativa y Guion Cinematografico
Exec=bash -c 'cd \"$SCRIPT_DIR\" && ./run.sh'
Icon=$SCRIPT_DIR/assets/icon_256.png
Terminal=false
Categories=Office;WordProcessor;Development;
StartupNotify=true
"

# 1. Agregar al menú de aplicaciones del sistema
mkdir -p "$HOME/.local/share/applications"
echo "$DESKTOP_ENTRY" > "$HOME/.local/share/applications/nelia.desktop"
chmod +x "$HOME/.local/share/applications/nelia.desktop"

# 2. Agregar al Escritorio
if [ -n "$DESKTOP_DIR" ]; then
    TARGET_DESKTOP="$DESKTOP_DIR/NELIA.desktop"
    echo "$DESKTOP_ENTRY" > "$TARGET_DESKTOP"
    chmod +x "$TARGET_DESKTOP"
    # Marcar como ejecutable confiable en GNOME
    gio set "$TARGET_DESKTOP" metadata::trusted true 2>/dev/null || true
    echo "✨ Icono creado con éxito en tu Escritorio: $TARGET_DESKTOP"
fi

echo "✨ NELIA ahora también aparece en tu menú de aplicaciones del sistema."
