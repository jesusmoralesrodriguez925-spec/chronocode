#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChronoCode v2 - Núcleo: bucle agéntico con herramientas y BYOK. Solo Termux por ahora.
Dependencias: requests, python-dotenv.
"""
import json
import os
import re
import shlex
import subprocess
from pathlib import Path

import requests
from dotenv import load_dotenv
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    PT_OK = True
except ImportError:
    PT_OK = False

load_dotenv(Path(__file__).resolve().parent / ".env")

# ---------------- Banner (idéntico al de chronocode.py) ----------------
console = Console(highlight=False)

FRAME_IDLE = [
    "    ▄████████▄       ",
    "    ██  ██  ██       ",
    "███ ██████████ ███   ",
    "▀▀▀ ██████████ ▀▀▀   ",
    "    ▀████████▀       ",
    "                     ",
]


def mostrar_banner(proveedores):
    """Dibuja una sola vez el banner: mascota a la izquierda, textos a la derecha."""
    mascota = Text("\n".join(FRAME_IDLE), style="bold green", no_wrap=True)
    derecha = Text()
    derecha.append("ChronoCode v1.0", style="bold green")
    derecha.append("\n>_ agente de IA para tu terminal", style="cyan")
    derecha.append("\nProveedores: " + proveedores, style="green")
    layout = Layout()
    layout.split_row(
        Layout(Align(mascota, align="left", vertical="middle"), name="mascota", size=23),
        Layout(Align(derecha, align="left", vertical="middle"), name="texto"),
    )
    console.print(Panel(layout, height=8, border_style="green", padding=(0, 1)))
    console.print(Text("Escribe / para ver los comandos.", style="dim green"))


# ---------------- Proveedores (BYOK) ----------------
PROVEEDORES = [
    {"nombre": "Groq", "env": "GROQ_API_KEY", "url": "https://api.groq.com/openai/v1/chat/completions",
     "modelo": "openai/gpt-oss-120b"},
    {"nombre": "OpenRouter", "env": "OPENROUTER_API_KEY", "url": "https://openrouter.ai/api/v1/chat/completions",
     "modelo": "meta-llama/llama-3.3-70b-instruct:free"},
    {"nombre": "OpenAI", "env": "OPENAI_API_KEY", "url": "https://api.openai.com/v1/chat/completions",
     "modelo": "gpt-4o-mini"},
    {"nombre": "Gemini", "env": "GEMINI_API_KEY",
     "url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
     "modelo": "gemini-2.5-flash"},
    {"nombre": "DeepSeek", "env": "DEEPSEEK_API_KEY", "url": "https://api.deepseek.com/chat/completions",
     "modelo": "deepseek-chat"},
]

MAX_PASOS = 10              # pasos de herramientas por petición
MAX_SALIDA = 4000           # caracteres máximos devueltos por una herramienta
TIMEOUT = 120

# ---------------- Seguridad ----------------
# Comandos que nunca se ejecutan
PROHIBIDOS = [
    r"rm\s+-[a-z]*r[a-z]*f?\s+/(\s|$|\*)", r"\bmkfs", r"\bdd\s+if=", r"\bshutdown\b", r"\breboot\b",
    r"\bsudo\b", r"chmod\s+-R\s+777\s+/", r":\(\)\s*\{", r"(curl|wget)[^|]*\|\s*(sh|bash)",
]
# Peticiones que el agente no debe ayudar a cumplir
TEMAS_NO_PERMITIDOS = (
    "malware", "ransomware", "keylogger", "robar contraseñas", "robar cuentas", "phishing",
    "ddos", "exploit para atacar", "atacar un sistema ajeno", "estafa", "fraude",
)

REGLAS = (
    "Eres ChronoCode, un asistente de programación. Responde en español. "
    "No ayudes a crear malware, robar cuentas o datos, atacar sistemas de terceros, hacer fraude "
    "ni nada ilegal: si la petición lo es, dilo y no uses herramientas. "
    "Para trabajar en archivos usa las herramientas; lee un archivo antes de editarlo. "
    "Cuando termines, responde con un resumen corto."
)


def es_prohibido(cmd):
    for patron in PROHIBIDOS:
        if re.search(patron, cmd):
            return f"comando bloqueado por seguridad ({patron})"
    return None


SENSIBLES = {".env", ".ssh", ".git", ".netrc", ".aws", ".gnupg"}


def ruta_permitida(path):
    """Solo rutas dentro de la carpeta de trabajo y sin archivos sensibles."""
    p = Path(path).expanduser().resolve()
    base = Path.cwd().resolve()
    if p != base and base not in p.parents:
        return False, "la ruta está fuera de la carpeta de trabajo"
    if any(parte in SENSIBLES for parte in p.parts):
        return False, "es un archivo sensible"
    return True, ""


ESTADO_SPINNER = {"activo": None}


def confirmar(pregunta):
    """Pregunta s/N. Pausa el spinner para que no tape la respuesta."""
    spinner = ESTADO_SPINNER["activo"]
    if spinner is not None:
        spinner.stop()
    try:
        return _leer_si_no(pregunta)
    finally:
        if spinner is not None:
            spinner.start()


def _leer_si_no(pregunta):
    try:
        return input(f"{pregunta} [s/N]: ").strip().lower() in ("s", "si", "sí", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


# ---------------- Herramientas ----------------
def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")[:MAX_SALIDA * 4]
    except OSError as e:
        return f"ERROR: {e}"


def write_file(path, content):
    ok, motivo = ruta_permitida(path)
    if not ok:
        return f"BLOQUEADO: {motivo}."
    print(f"\n--- Escribir {path} ---\n{content[:1500]}\n")
    if not confirmar(f"¿Guardar {path}?"):
        return "CANCELADO por el usuario."
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
        return f"OK: {path} guardado."
    except OSError as e:
        return f"ERROR: {e}"


def edit_file(path, old_string, new_string):
    ok, motivo = ruta_permitida(path)
    if not ok:
        return f"BLOQUEADO: {motivo}."
    try:
        texto = Path(path).read_text(encoding="utf-8")
    except OSError as e:
        return f"ERROR: {e}"
    veces = texto.count(old_string)
    if veces != 1:
        return f"ERROR: el texto aparece {veces} veces (debe aparecer exactamente 1)."
    print(f"\n--- Editar {path} ---\n- {old_string[:300]}\n+ {new_string[:300]}\n")
    if not confirmar(f"¿Aplicar el cambio en {path}?"):
        return "CANCELADO por el usuario."
    Path(path).write_text(texto.replace(old_string, new_string, 1), encoding="utf-8")
    return f"OK: cambio aplicado en {path}."


def run_command(cmd):
    motivo = es_prohibido(cmd)
    if motivo:
        return f"BLOQUEADO: {motivo}"
    print(f"\n$ {cmd}")
    if not confirmar("¿Ejecutar este comando?"):
        return "CANCELADO por el usuario."
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        salida = (r.stdout + r.stderr).strip() or "(sin salida)"
        return f"{salida[-MAX_SALIDA:]}\n[exit {r.returncode}]"
    except subprocess.TimeoutExpired:
        return "ERROR: el comando tardó demasiado."


def run_tests():
    """Detecta y ejecuta las pruebas del proyecto."""
    if Path("package.json").is_file() and '"test"' in Path("package.json").read_text(encoding="utf-8"):
        return run_command("npm test")
    if any(Path(".").glob("test_*.py")) or Path("tests").is_dir():
        return run_command("python3 -m pytest -q || python3 -m unittest discover -q")
    return "No encontré pruebas (package.json con 'test', test_*.py o carpeta tests/)."


HERRAMIENTAS = {
    "read_file": read_file, "write_file": write_file, "edit_file": edit_file,
    "run_command": run_command, "run_tests": run_tests,
}


def _esquema(nombre, descripcion, props=None, requeridos=None):
    return {"type": "function", "function": {
        "name": nombre, "description": descripcion,
        "parameters": {"type": "object", "properties": props or {}, "required": requeridos or []}}}


ESQUEMAS = [
    _esquema("read_file", "Lee un archivo de texto.",
             {"path": {"type": "string"}}, ["path"]),
    _esquema("write_file", "Crea o reemplaza un archivo (el usuario debe aprobarlo).",
             {"path": {"type": "string"}, "content": {"type": "string"}}, ["path", "content"]),
    _esquema("edit_file", "Reemplaza un texto exacto y único dentro de un archivo (el usuario debe aprobarlo).",
             {"path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}},
             ["path", "old_string", "new_string"]),
    _esquema("run_command", "Ejecuta un comando de Linux/Termux (el usuario debe aprobarlo).",
             {"cmd": {"type": "string"}}, ["cmd"]),
    _esquema("run_tests", "Ejecuta las pruebas del proyecto. Úsala después de cambiar código."),
]


def ejecutar(nombre, args):
    if nombre not in HERRAMIENTAS:
        return f"ERROR: herramienta desconocida '{nombre}'."
    try:
        return str(HERRAMIENTAS[nombre](**args))
    except TypeError as e:
        return f"ERROR en argumentos: {e}"


# ---------------- Bucle agéntico ----------------
def proveedores_activos():
    return [p for p in PROVEEDORES if os.getenv(p["env"], "").strip()]


def llamar_modelo(prov, mensajes):
    headers = {"Authorization": f"Bearer {os.getenv(prov['env']).strip()}",
               "Content-Type": "application/json"}
    payload = {"model": prov["modelo"], "messages": mensajes, "tools": ESQUEMAS, "tool_choice": "auto"}
    r = requests.post(prov["url"], headers=headers, json=payload, timeout=TIMEOUT)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:150]}")
    return r.json()["choices"][0]["message"]


def responder(historial):
    """Repite: pide al modelo, ejecuta herramientas, devuelve resultados, hasta texto final."""
    provs = proveedores_activos()
    if not provs:
        return "No hay ninguna API Key en .env (por ejemplo GROQ_API_KEY=...)."
    mensajes = [{"role": "system", "content": REGLAS}] + historial
    for _ in range(MAX_PASOS):
        msg = None
        for prov in provs:
            try:
                msg = llamar_modelo(prov, mensajes)
                break
            except (requests.RequestException, RuntimeError, KeyError) as e:
                print(f"[{prov['nombre']}] no disponible: {str(e)[:120]}. Pruebo el siguiente.")
        if msg is None:
            return "Ningún proveedor respondió. Revisa tus claves o inténtalo más tarde."
        llamadas = msg.get("tool_calls") or []
        if not llamadas:
            texto = (msg.get("content") or "").strip()
            historial.append({"role": "assistant", "content": texto})
            return texto
        mensajes.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": llamadas})
        for llamada in llamadas:
            try:
                args = json.loads(llamada["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = None
            nombre = llamada["function"]["name"]
            print(f"  → {nombre}")
            resultado = "ERROR: argumentos inválidos." if args is None else ejecutar(nombre, args)
            mensajes.append({"role": "tool", "tool_call_id": llamada["id"], "content": resultado})
    return "Se alcanzó el límite de pasos para esta petición."


COMANDOS = [
    ("/help", "Muestra los comandos"),
    ("/clear", "Borra el chat"),
    ("/exit", "Sale del agente"),
]

if PT_OK:
    class ComandosCompleter(Completer):
        """Al escribir "/" muestra el menú y lo filtra mientras escribes."""

        def get_completions(self, document, complete_event):
            texto = document.text_before_cursor
            if not texto.startswith("/") or " " in texto:
                return
            for cmd, desc in COMANDOS:
                if cmd.startswith(texto):
                    yield Completion(cmd, start_position=-len(texto), display_meta=desc)

    _sesion = PromptSession(completer=ComandosCompleter(), complete_while_typing=True)


def leer_linea():
    """Lee la petición del usuario, con menú de comandos si está disponible."""
    if PT_OK:
        return _sesion.prompt("\n> ").strip()
    return input("\n> ").strip()


def mostrar_ayuda():
    console.print(Text("Comandos:", style="bold green"))
    for cmd, desc in COMANDOS:
        console.print(Text(f"  {cmd:<8} {desc}"))
    console.print(Text("Cualquier otro texto se envía al agente.", style="dim"))


def main():
    nombres = " > ".join(p["nombre"] for p in proveedores_activos()) or "ninguno"
    mostrar_banner(nombres)
    historial = []
    while True:
        try:
            linea = leer_linea()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not linea:
            continue
        if linea in ("/exit", "salir"):
            break
        if linea == "/help":
            mostrar_ayuda()
            continue
        if linea == "/clear":
            historial.clear()
            print("Chat borrado.")
            continue
        if any(tema in linea.lower() for tema in TEMAS_NO_PERMITIDOS):
            console.print(Text("No puedo ayudar con eso: es una actividad ilegal o dañina. "
                               "Si es para aprender ciberseguridad de forma legal, puedo "
                               "explicarte cómo proteger un sistema propio.", style="yellow"))
            continue
        historial.append({"role": "user", "content": linea})
        estado = console.status("ChronoCode pensando...", spinner="dots")
        ESTADO_SPINNER["activo"] = estado
        estado.start()
        try:
            respuesta = responder(historial)
        finally:
            estado.stop()
            ESTADO_SPINNER["activo"] = None
        console.print(Markdown(respuesta, code_theme="monokai"))


if __name__ == "__main__":
    main()
