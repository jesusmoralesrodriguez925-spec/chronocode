#!/usr/bin/env bash
# ChronoCode - instalador. Funciona en Termux, Debian/Ubuntu, Fedora, Arch y macOS.
set -e

echo "==> Instalando ChronoCode..."

if [ -n "$TERMUX_VERSION" ] || command -v pkg >/dev/null 2>&1 && [ -d "/data/data/com.termux" ]; then
  echo "==> Termux detectado"
  pkg update -y && pkg upgrade -y
  pkg install -y python git
elif command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y python3 python3-pip git
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y python3 python3-pip git
elif command -v pacman >/dev/null 2>&1; then
  sudo pacman -Sy --noconfirm python python-pip git
elif command -v brew >/dev/null 2>&1; then
  brew install python git
else
  echo "No reconozco tu gestor de paquetes. Instala Python 3 manualmente y vuelve a ejecutar."
  exit 1
fi

PY=python3
command -v python3 >/dev/null 2>&1 || PY=python

echo "==> Instalando dependencias de Python..."
$PY -m pip install --upgrade requests python-dotenv 2>/dev/null \
  || $PY -m pip install --user --upgrade requests python-dotenv 2>/dev/null \
  || $PY -m pip install --user --break-system-packages --upgrade requests python-dotenv

touch .gitignore
grep -qxF ".env" .gitignore || echo ".env" >> .gitignore

echo ""
echo "Listo. Ejecuta:  $PY chronocode.py"
echo "Al primer inicio te pedirá tu API Key (Gemini: https://aistudio.google.com/apikey)."
