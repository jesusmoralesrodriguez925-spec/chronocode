#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools.py - Capa de herramientas de ChronoCode (Fase 1).

Herramientas que el modelo podrá usar:
  read_file, write_file, edit_file, glob, grep, run_command.

Dispatcher: ejecutar_herramienta(nombre, argumentos) -> str.
Este módulo NO importa chronocode.py. La denylist, la ejecución de
comandos y la consola se inyectan con configurar() desde chronocode.py.
"""
import difflib
import json
import time
import glob as _glob
import os
import re
import shutil
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# ---------------------------------------------------------------------
#  Configuración inyectada desde chronocode.py
# ---------------------------------------------------------------------
_config = {
    "console": Console(highlight=False),
    "es_seguro": None,        # función(cmd) -> (bool, motivo)   (denylist)
    "ejecutar_shell": None,   # función(cmd) -> CompletedProcess
}

MAX_LECTURA = 20000           # caracteres máximos devueltos por read_file
MAX_RESULTADOS = 200          # coincidencias máximas en glob y grep
AFIRMATIVAS = ("s", "si", "sí", "y", "yes")
LEXER_POR_EXT = {
    "py": "python", "js": "javascript", "ts": "typescript", "html": "html",
    "css": "css", "json": "json", "md": "markdown", "sh": "bash", "txt": "text",
    "yml": "yaml", "yaml": "yaml", "toml": "toml", "sql": "sql",
}


def configurar(console=None, es_seguro=None, ejecutar_shell=None):
    """Recibe desde chronocode.py la consola, la denylist y el ejecutor de comandos."""
    if console is not None:
        _config["console"] = console
    if es_seguro is not None:
        _config["es_seguro"] = es_seguro
    if ejecutar_shell is not None:
        _config["ejecutar_shell"] = ejecutar_shell


def _pedir_confirmacion(pregunta):
    """Pregunta [s/N]. Por defecto es NO."""
    try:
        respuesta = _config["console"].input(f"[magenta]{pregunta} [s/N]: [/]")
    except (EOFError, KeyboardInterrupt):
        return False
    return respuesta.strip().lower() in AFIRMATIVAS


# ---------------------------------------------------------------------
#  Herramientas
# ---------------------------------------------------------------------
BACKUP_DIR = Path(".chronocode_backups")
INDICE = BACKUP_DIR / "index.json"


def _leer_indice():
    if not INDICE.exists():
        return []
    try:
        return json.loads(INDICE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _guardar_indice(indice):
    BACKUP_DIR.mkdir(exist_ok=True)
    INDICE.write_text(json.dumps(indice, ensure_ascii=False, indent=2), encoding="utf-8")


def _respaldar(path_str):
    """Guarda una copia del archivo antes de cambiarlo (o anota que era nuevo)."""
    p = Path(path_str).expanduser().resolve()
    BACKUP_DIR.mkdir(exist_ok=True)
    indice = _leer_indice()
    if p.exists():
        marca = time.strftime("%Y%m%d-%H%M%S")
        destino = BACKUP_DIR / f"{marca}_{len(indice)}_{p.name}"
        shutil.copy2(p, destino)
        indice.append({"path": str(p), "backup": str(destino), "nuevo": False})
    else:
        indice.append({"path": str(p), "backup": None, "nuevo": True})
    _guardar_indice(indice)


def rewind():
    """Deshace el cambio más reciente hecho por write_file o edit_file."""
    indice = _leer_indice()
    if not indice:
        return "No hay cambios para restaurar."
    ultimo = indice.pop()
    p = Path(ultimo["path"])
    try:
        if ultimo["nuevo"]:
            if p.exists():
                p.unlink()
            mensaje = f"Eliminado el archivo que se había creado: {p}"
        else:
            shutil.copy2(ultimo["backup"], p)
            mensaje = f"Restaurado: {p}"
    except OSError as e:
        return f"ERROR al restaurar: {e}"
    _guardar_indice(indice)
    return mensaje


def read_file(path: str) -> str:
    """Lee un archivo de texto y devuelve su contenido."""
    try:
        p = Path(path).expanduser()
        if not p.is_file():
            return f"ERROR: no existe el archivo '{path}'."
        texto = p.read_text(encoding="utf-8", errors="replace")
        if len(texto) > MAX_LECTURA:
            texto = texto[:MAX_LECTURA] + "\n[... archivo truncado ...]"
        return texto
    except OSError as e:
        return f"ERROR al leer '{path}': {e}"


def write_file(path: str, content: str) -> str:
    """Escribe un archivo tras mostrarlo y pedir confirmación [s/N]."""
    consola = _config["console"]
    p = Path(path).expanduser()
    lexer = LEXER_POR_EXT.get(p.suffix.lower().lstrip("."), "text")
    consola.print(Panel(Syntax(content, lexer, theme="monokai", line_numbers=True),
                        title=f"Escribir: {path}", title_align="left", border_style="yellow"))
    if not _pedir_confirmacion(f"¿Guardar en {path}?"):
        return f"CANCELADO: el usuario no aprobó escribir '{path}'."
    try:
        _respaldar(path)
    except OSError as e:
        return f"ERROR al crear la copia de seguridad: {e}"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8", newline="\n")
    except OSError as e:
        return f"ERROR al escribir '{path}': {e}"
    return f"OK: archivo guardado ({len(content.splitlines())} líneas): {path}"


def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Reemplaza un texto exacto por otro. Pide confirmación [s/N] antes de guardar."""
    if not old_string:
        return "ERROR: old_string no puede estar vacío."
    p = Path(path).expanduser()
    if not p.is_file():
        return f"ERROR: no existe el archivo '{path}'."
    try:
        original = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"ERROR al leer '{path}': {e}"

    veces = original.count(old_string)
    if veces == 0:
        return "ERROR: no se encontró el texto exacto en el archivo. Revisa espacios y saltos de línea."
    if veces > 1:
        return (f"ERROR: el texto aparece {veces} veces. "
                "Incluye más contexto alrededor para que sea único.")

    nuevo = original.replace(old_string, new_string, 1)
    diff = "\n".join(difflib.unified_diff(
        original.splitlines(), nuevo.splitlines(),
        fromfile=f"{path} (actual)", tofile=f"{path} (propuesto)", lineterm="", n=2))
    _config["console"].print(Panel(Syntax(diff or "(sin cambios)", "diff", theme="ansi_dark"),
                                   title=f"Editar: {path}", title_align="left", border_style="yellow"))
    if not _pedir_confirmacion(f"¿Aplicar este cambio en {path}?"):
        return f"CANCELADO: el usuario no aprobó editar '{path}'."
    try:
        _respaldar(path)
    except OSError as e:
        return f"ERROR al crear la copia de seguridad: {e}"
    try:
        p.write_text(nuevo, encoding="utf-8", newline="\n")
    except OSError as e:
        return f"ERROR al escribir '{path}': {e}"
    return f"OK: cambio aplicado en {path}."


def glob(pattern: str, root: str = ".") -> str:
    """Busca archivos que coincidan con un patrón (ej. '**/*.py')."""
    rutas = sorted(_glob.glob(os.path.join(root, pattern), recursive=True))
    if not rutas:
        return "Sin coincidencias."
    extra = "" if len(rutas) <= MAX_RESULTADOS else f"\n[... {len(rutas) - MAX_RESULTADOS} más ...]"
    return "\n".join(rutas[:MAX_RESULTADOS]) + extra


def grep(pattern: str, path: str = ".") -> str:
    """Busca un patrón (expresión regular) dentro de archivos. Usa ripgrep si está instalado."""
    rg = shutil.which("rg")
    if rg:
        try:
            r = subprocess.run([rg, "-n", "--max-count", "50", "--", pattern, path],
                               capture_output=True, text=True, timeout=20)
            salida = r.stdout.strip()
            return salida[:4000] or "Sin coincidencias."
        except (subprocess.TimeoutExpired, OSError) as e:
            return f"ERROR en grep: {e}"

    # Respaldo en Python si no hay ripgrep
    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"ERROR: expresión regular inválida: {e}"
    encontrados = []
    base = Path(path).expanduser()
    archivos = [base] if base.is_file() else base.rglob("*")
    for archivo in archivos:
        if not archivo.is_file() or any(parte in {".git", "node_modules", "__pycache__"}
                                        for parte in archivo.parts):
            continue
        try:
            if archivo.stat().st_size > 1_000_000:
                continue
            for n, linea in enumerate(archivo.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if regex.search(linea):
                    encontrados.append(f"{archivo}:{n}:{linea.strip()}")
                    if len(encontrados) >= MAX_RESULTADOS:
                        return "\n".join(encontrados) + "\n[... resultados truncados ...]"
        except OSError:
            continue
    return "\n".join(encontrados) or "Sin coincidencias."


def run_command(cmd: str) -> str:
    """Ejecuta un comando de terminal: denylist -> confirmación [s/N] -> ejecución."""
    es_seguro = _config["es_seguro"]
    ejecutar = _config["ejecutar_shell"]
    if es_seguro is None or ejecutar is None:
        return "ERROR: la herramienta de comandos no está configurada."

    cmd = cmd.strip()
    if not cmd:
        return "ERROR: comando vacío."
    seguro, motivo = es_seguro(cmd)
    if not seguro:
        return f"BLOQUEADO por seguridad: {motivo}"

    _config["console"].print(Panel(f"$ {cmd}", title="Comando propuesto", title_align="left",
                                   border_style="yellow", expand=False))
    if not _pedir_confirmacion("¿Ejecutar este comando?"):
        return "CANCELADO: el usuario no aprobó el comando."
    try:
        r = ejecutar(cmd)
    except subprocess.TimeoutExpired:
        return "ERROR: el comando superó el tiempo máximo."
    except OSError as e:
        return f"ERROR al ejecutar: {e}"
    salida = ((r.stdout or "") + (r.stderr or "")).strip()
    return f"{salida[:4000] or '(sin salida)'}\n[exit {r.returncode}]"


# ---------------------------------------------------------------------
#  Registro y dispatcher
# ---------------------------------------------------------------------
TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "glob": glob,
    "grep": grep,
    "run_command": run_command,
}

# Descripción para el LLM (se usará en la Fase 2)
TOOL_SCHEMAS = [
    {"name": "read_file", "description": "Lee un archivo de texto.",
     "parameters": {"path": "string"}},
    {"name": "write_file", "description": "Crea o sobrescribe un archivo (pide confirmación).",
     "parameters": {"path": "string", "content": "string"}},
    {"name": "edit_file", "description": "Reemplaza un texto exacto y único dentro de un archivo.",
     "parameters": {"path": "string", "old_string": "string", "new_string": "string"}},
    {"name": "glob", "description": "Lista archivos que coinciden con un patrón.",
     "parameters": {"pattern": "string", "root": "string (opcional)"}},
    {"name": "grep", "description": "Busca un patrón regex dentro de archivos.",
     "parameters": {"pattern": "string", "path": "string (opcional)"}},
    {"name": "run_command", "description": "Ejecuta un comando de terminal (con revisión y confirmación).",
     "parameters": {"cmd": "string"}},
]


def ejecutar_herramienta(nombre: str, argumentos: dict) -> str:
    """Punto de entrada del dispatcher. Nunca lanza excepciones: devuelve texto de error."""
    if nombre not in TOOLS:
        return f"ERROR: herramienta desconocida '{nombre}'. Disponibles: {', '.join(TOOLS)}."
    try:
        return str(TOOLS[nombre](**(argumentos or {})))
    except TypeError as e:
        return f"ERROR en los argumentos de '{nombre}': {e}"
    except Exception as e:
        return f"ERROR en '{nombre}': {type(e).__name__}: {e}"
