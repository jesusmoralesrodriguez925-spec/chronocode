#!/usr/bin/env bash
# ChronoCode - instalador de alias global.
# Uso: bash install.sh
# No instala paquetes ni librerías. Solo crea el comando "chronocode".
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$DIR/chronocode.py"

if [ ! -f "$SCRIPT" ]; then
  echo "No encuentro chronocode.py en $DIR"
  exit 1
fi

# Elige el intérprete de Python disponible
PY=""
for cand in python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then
  echo "No encuentro Python. Instálalo tú y vuelve a ejecutar este script."
  exit 1
fi

OS="$(uname -s 2>/dev/null || echo unknown)"
case "$OS" in
  MINGW*|MSYS*|CYGWIN*)  # Git Bash / MSYS en Windows
    BIN_DIR="$HOME/bin"
    mkdir -p "$BIN_DIR"
    cat > "$BIN_DIR/chronocode.bat" <<EOF
@echo off
"$PY" "$SCRIPT" %*
EOF
    # Asegura que ~/bin esté en el PATH de Git Bash
    RC="$HOME/.bashrc"
    grep -qF 'export PATH="$HOME/bin:$PATH"' "$RC" 2>/dev/null || \
      echo 'export PATH="$HOME/bin:$PATH"' >> "$RC"
    grep -qF "alias chronocode=" "$RC" 2>/dev/null || \
      echo "alias chronocode='$PY \"$SCRIPT\"'" >> "$RC"
    echo "Windows: creado $BIN_DIR/chronocode.bat"
    echo "Abre una terminal nueva y escribe: chronocode"
    ;;
  *)  # Linux, macOS, Termux
    RC="$HOME/.bashrc"
    case "${SHELL:-}" in
      *zsh) RC="$HOME/.zshrc" ;;
    esac
    touch "$RC"
    # Quita un alias anterior de ChronoCode para no duplicarlo
    sed -i.bak '/# ChronoCode alias/d; /alias chronocode=/d' "$RC" 2>/dev/null || true
    rm -f "$RC.bak"
    {
      echo "# ChronoCode alias"
      echo "alias chronocode='$PY \"$SCRIPT\"'"
    } >> "$RC"
    echo "Alias creado en $RC"
    echo "Cierra la terminal (en Termux, cierra la app por completo) y escribe: chronocode"
    ;;
esac
