#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChronoCode - Agente de programación para la terminal. Open Source, BYOK.
Sin backend, sin base de datos, sin servidores propios.
Dependencias: librería estándar + requests + python-dotenv.
Proveedores: Groq, OpenRouter, OpenAI, Anthropic, Gemini (tu propia API Key).

Uso:  python chronocode.py [archivo]
Comandos: /file /run /key /stream /clear /help /exit   (atajo: !cmd)
"""
import os
import re
import sys
import json
import time
import shutil
import difflib
import subprocess
from pathlib import Path

try:
    import requests
except ImportError:
    print("Falta 'requests'. Instálalo con:  pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Falta 'python-dotenv'. Instálalo con:  pip install python-dotenv")
    sys.exit(1)

try:
    import readline  # noqa: F401  (historial con flechas; opcional)
except ImportError:
    pass

# =====================================================================
#  CONFIGURACIÓN
# =====================================================================
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

KEY_VARS = {
    "Groq": "GROQ_API_KEY",
    "OpenRouter": "OPENROUTER_API_KEY",
    "OpenAI": "OPENAI_API_KEY",
    "Anthropic": "ANTHROPIC_API_KEY",
    "Gemini": "GEMINI_API_KEY",
}

# Modelos: se pueden cambiar desde el .env sin tocar el código.
# Los catálogos (sobre todo los ":free" de OpenRouter) cambian a menudo: verifica nombres vigentes.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.3-70b-versatile")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
OPENROUTER_FALLBACK_MODEL = os.getenv("OPENROUTER_FALLBACK_MODEL", "openai/gpt-oss-120b:free")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash")
ANTHROPIC_MAX_TOKENS = 8192

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
              "{model}:streamGenerateContent?alt=sse")

# Orden por defecto. Cámbialo con CHRONO_PROVIDER_ORDER="gemini,groq" en el .env
DEFAULT_ORDER = ["Groq", "OpenRouter", "OpenAI", "Anthropic", "Gemini"]

STREAM = True
CONNECT_TIMEOUT = int(os.getenv("CHRONO_CONNECT_TIMEOUT", "20"))   # segundos para conectar
READ_TIMEOUT = int(os.getenv("CHRONO_READ_TIMEOUT", "120"))        # segundos esperando datos
MAX_RETRIES = 3             # reintentos por modelo (red lenta, timeouts, 5xx)
MAX_HISTORY = 20
MAX_FILE_CHARS = 15000
MAX_OUTPUT_CHARS = 4000
COMMAND_TIMEOUT = 60

SYSTEM_PROMPT = """Eres ChronoCode, un experto programador. Respuestas cortas, directas y enfocadas en código.

FORMATO PARA GUARDAR ARCHIVOS (obligatorio):
Si necesitas crear o modificar un archivo, usa este formato exacto:
```chronocode:RUTA/DEL/ARCHIVO.ext
(contenido COMPLETO del archivo)
```

Para comandos de terminal usa un bloque normal (```bash), nunca chronocode:.

Reglas:
- Un bloque chronocode por archivo; siempre el archivo completo.
- Bloques normales (python, bash) solo para fragmentos, ejemplos o comandos.
- No expliques de más: unas pocas líneas fuera de los bloques.
- Responde siempre en español y explica brevemente qué hace el código y cómo probarlo.
"""

# =====================================================================
#  TERMINAL
# =====================================================================
if os.name == "nt":
    os.system("")

USE_COLOR = sys.stdout.isatty()


def c(text, code):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def info(m): print(c(m, "36"))
def warn(m): print(c(m, "33"))
def err(m): print(c(m, "31"))
def ok(m): print(c(m, "32"))


def ask_yes_no(question, default=False):
    suffix = " [S/n]: " if default else " [s/N]: "
    try:
        ans = input(c(question, "35") + suffix).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if not ans:
        return default
    return ans in ("s", "si", "sí", "y", "yes")


class State:
    def __init__(self):
        self.current_file = None
        self.history = []


STATE = State()

# =====================================================================
#  ARCHIVOS
# =====================================================================
def read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError as e:
        err(f"No se pudo leer '{path}': {e}")
        return None


def set_context_file(path):
    path = os.path.expanduser(path.strip().strip('"').strip("'"))
    if not path:
        return False
    if os.path.isfile(path):
        STATE.current_file = path
        n = len((read_file(path) or "").splitlines())
        ok(f"Archivo cargado: {path} ({n} líneas)")
        return True
    if os.path.exists(path):
        err(f"'{path}' no es un archivo.")
        return False
    warn(f"'{path}' no existe todavía.")
    if ask_yes_no("¿Usarlo como archivo de trabajo (se creará al guardar)?"):
        STATE.current_file = path
        return True
    return False


def build_system_message():
    parts = [SYSTEM_PROMPT,
             f"\nEntorno: SO={sys.platform}, directorio={os.getcwd()}, "
             f"Python={sys.version.split()[0]}."]
    if STATE.current_file:
        content = read_file(STATE.current_file) if os.path.isfile(STATE.current_file) else None
        if content is not None:
            if len(content) > MAX_FILE_CHARS:
                content = content[:MAX_FILE_CHARS] + "\n[... archivo truncado ...]"
            parts.append(f"\nArchivo en contexto: {STATE.current_file}\n"
                         f"----- INICIO -----\n{content}\n----- FIN -----")
        else:
            parts.append(f"\nArchivo de trabajo (aún inexistente): {STATE.current_file}")
    return "\n".join(parts)


# =====================================================================
#  PROVEEDORES
# =====================================================================
def _has(v):
    return bool(v and v.strip())


def _key(name):
    return os.getenv(KEY_VARS[name])


class StreamResult:
    def __init__(self, provider=""):
        self.provider = provider
        self.text = ""
        self.started = False
        self.complete = False


def _header_once(res):
    if not res.started:
        res.started = True
        print()
        print(c(f"ChronoCode [{res.provider}]:", "1;34"))


def _err_text(e):
    return e.get("message", str(e)) if isinstance(e, dict) else str(e)


# Extractores SSE -> (texto, terminó, error)
def _extract_openai(obj):
    if obj.get("error"):
        return None, False, _err_text(obj["error"])
    ch = obj.get("choices") or []
    if not ch:
        return None, False, None
    return (ch[0].get("delta") or {}).get("content"), bool(ch[0].get("finish_reason")), None


def _extract_anthropic(obj):
    t = obj.get("type")
    if t == "error":
        return None, False, _err_text(obj.get("error", obj))
    if t == "content_block_delta":
        d = obj.get("delta") or {}
        if d.get("type") == "text_delta":
            return d.get("text"), False, None
    if t == "message_stop":
        return None, True, None
    return None, False, None


def _extract_gemini(obj):
    if obj.get("error"):
        return None, False, _err_text(obj["error"])
    cands = obj.get("candidates") or []
    if not cands:
        block = (obj.get("promptFeedback") or {}).get("blockReason")
        return None, False, (f"petición bloqueada ({block})" if block else None)
    cand = cands[0]
    parts = (cand.get("content") or {}).get("parts") or []
    piece = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    return (piece or None), bool(cand.get("finishReason")), None


def _merge_roles(msgs):
    out = []
    for m in msgs:
        if out and out[-1]["role"] == m["role"]:
            out[-1]["content"] += "\n\n" + m["content"]
        else:
            out.append({"role": m["role"], "content": m["content"]})
    return out


def _build_openai_like(url, key, model, messages, temperature, extra_headers=None):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "User-Agent": "ChronoCode/1.0"}
    if extra_headers:
        headers.update(extra_headers)
    payload = {"model": model, "messages": messages, "stream": True}
    if temperature is not None:
        payload["temperature"] = temperature
    return url, headers, payload, _extract_openai


def _build_groq(key, model, messages):
    return _build_openai_like(GROQ_URL, key, model, messages, 0.2)


def _build_openrouter(key, model, messages):
    extra = {"X-Title": "ChronoCode"}   # cabecera opcional de OpenRouter
    return _build_openai_like(OPENROUTER_URL, key, model, messages, 0.2, extra)


def _build_openai(key, model, messages):
    return _build_openai_like(OPENAI_URL, key, model, messages, None)


def _build_anthropic(key, model, messages):
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    msgs = _merge_roles([m for m in messages if m["role"] != "system"])
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01",
               "Content-Type": "application/json", "User-Agent": "ChronoCode/1.0"}
    payload = {"model": model, "max_tokens": ANTHROPIC_MAX_TOKENS, "system": system,
               "messages": msgs, "stream": True}
    return ANTHROPIC_URL, headers, payload, _extract_anthropic


def _build_gemini(key, model, messages):
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    msgs = _merge_roles([m for m in messages if m["role"] != "system"])
    contents = [{"role": "model" if m["role"] == "assistant" else "user",
                 "parts": [{"text": m["content"]}]} for m in msgs]
    headers = {"x-goog-api-key": key, "Content-Type": "application/json",
               "User-Agent": "ChronoCode/1.0"}
    payload = {"system_instruction": {"parts": [{"text": system}]}, "contents": contents}
    return GEMINI_URL.format(model=model), headers, payload, _extract_gemini


def available_providers():
    specs = {
        "Groq": ([GROQ_MODEL, GROQ_FALLBACK_MODEL], _build_groq),
        "OpenRouter": ([OPENROUTER_MODEL, OPENROUTER_FALLBACK_MODEL], _build_openrouter),
        "OpenAI": ([OPENAI_MODEL], _build_openai),
        "Anthropic": ([ANTHROPIC_MODEL], _build_anthropic),
        "Gemini": ([GEMINI_MODEL, GEMINI_FALLBACK_MODEL], _build_gemini),
    }
    custom = [x.strip().lower() for x in os.getenv("CHRONO_PROVIDER_ORDER", "").split(",") if x.strip()]
    order = [n for p in custom for n in DEFAULT_ORDER if n.lower() == p]
    order += [n for n in DEFAULT_ORDER if n not in order]
    provs = []
    for name in order:
        if _has(_key(name)):
            models, build = specs[name]
            uniq = []
            for m in models:
                if m and m not in uniq:
                    uniq.append(m)
            provs.append({"name": name, "key": _key(name).strip(), "models": uniq, "build": build})
    return provs


# =====================================================================
#  RED: SSE + manejo de errores y timeouts
# =====================================================================
def _consume_sse(r, res, extract):
    live = STREAM
    r.encoding = "utf-8"

    def fail(reason):
        if not live:
            res.text = ""
        return False, reason, 0

    try:
        for raw in r.iter_lines(decode_unicode=True):
            if not raw or raw.startswith(":") or not raw.startswith("data:"):
                continue   # keep-alives (OpenRouter envía ": OPENROUTER PROCESSING") y líneas vacías
            data = raw[5:].strip()
            if data == "[DONE]":
                res.complete = True
                break
            try:
                obj = json.loads(data)
            except ValueError:
                continue
            if not isinstance(obj, dict):
                continue
            piece, done, error = extract(obj)
            if error:
                return fail(f"error del proveedor: {error}")
            if piece:
                res.text += piece
                if live:
                    _header_once(res)
                    sys.stdout.write(piece)
                    sys.stdout.flush()
            if done:
                res.complete = True
    except requests.exceptions.Timeout:
        return fail("tiempo de espera agotado durante la respuesta")
    except requests.exceptions.RequestException:
        return fail("la conexión se cortó durante la respuesta")
    except (ValueError, UnicodeDecodeError):
        return fail("datos corruptos durante la respuesta")

    if not res.text.strip():
        return False, "respuesta vacía", 0
    if not live:
        _header_once(res)
        print(res.text.strip())
    return True, None, 0


def _http_request(url, headers, payload, extract, res):
    """Devuelve (exito, motivo|None, espera_s).
    Prefijos: __skip_provider__ (clave/bloqueo), __skip_model__ (probar otro modelo)."""
    try:
        r = requests.post(url, headers=headers, json=payload,
                          timeout=(CONNECT_TIMEOUT, READ_TIMEOUT), stream=True)
    except requests.exceptions.ConnectTimeout:
        return False, f"no se pudo conectar en {CONNECT_TIMEOUT}s", 0
    except requests.exceptions.ReadTimeout:
        return False, f"el servidor no respondió en {READ_TIMEOUT}s", 0
    except requests.exceptions.Timeout:
        return False, "tiempo de espera agotado", 0
    except requests.exceptions.ConnectionError:
        return False, "sin conexión o conexión inestable", 0
    except requests.exceptions.RequestException as e:
        return False, f"error de red: {e}", 0

    with r:
        code = r.status_code
        if code in (401, 403):
            return False, f"__skip_provider__:acceso denegado (HTTP {code}): clave inválida o servicio no disponible desde tu región", 0
        if code == 402:
            return False, "__skip_provider__:sin créditos o pago requerido (HTTP 402)", 0
        if code == 429:
            return False, "__skip_model__:límite de uso alcanzado (HTTP 429)", 0
        if code == 408 or code >= 500:
            wait = 0
            try:
                wait = min(int(r.headers.get("Retry-After", 0)), 30)
            except ValueError:
                pass
            return False, f"servidor ocupado (HTTP {code})", wait
        if code != 200:
            return False, f"__skip_model__:HTTP {code} {r.text[:150].strip()}", 0
        return _consume_sse(r, res, extract)


def _run_providers(providers, messages):
    for i, prov in enumerate(providers):
        skip_provider = False
        for model in prov["models"]:
            for attempt in range(1, MAX_RETRIES + 1):
                res = StreamResult(prov["name"])
                url, headers, payload, extract = prov["build"](prov["key"], model, messages)
                try:
                    success, reason, wait = _http_request(url, headers, payload, extract, res)
                except KeyboardInterrupt:
                    print()
                    if res.text:
                        warn("Respuesta interrumpida.")
                        return res
                    warn("Cancelado.")
                    return None

                if success:
                    print()
                    return res
                if res.text:
                    print()
                    warn(f"Respuesta cortada ({reason}). Se conserva lo recibido.")
                    return res
                if reason.startswith("__skip_provider__"):
                    warn(f"[{prov['name']}] {reason.split(':', 1)[1]}")
                    skip_provider = True
                    break
                if reason.startswith("__skip_model__"):
                    warn(f"[{prov['name']} · {model}] {reason.split(':', 1)[1]}")
                    break
                if attempt < MAX_RETRIES:
                    delay = max(wait, 2 ** attempt)
                    warn(f"[{prov['name']}] intento {attempt}/{MAX_RETRIES} falló: {reason}. "
                         f"Reintentando en {delay}s...")
                    try:
                        time.sleep(delay)
                    except KeyboardInterrupt:
                        warn("Cancelado.")
                        return None
                else:
                    warn(f"[{prov['name']} · {model}] agotó {MAX_RETRIES} intentos: {reason}.")
            if skip_provider:
                break
        if i + 1 < len(providers):
            warn(f"Cambiando al siguiente proveedor: {providers[i + 1]['name']}...")

    err("Ningún proveedor respondió. Revisa tu conexión, tus límites de uso y tus claves (/key).")
    return None


def trim_history():
    if len(STATE.history) > MAX_HISTORY:
        STATE.history = STATE.history[-MAX_HISTORY:]
        while STATE.history and STATE.history[0]["role"] != "user":
            STATE.history.pop(0)


def get_llm_response(prompt):
    providers = available_providers()
    if not providers:
        err("No hay ninguna API Key configurada. Usa /key para añadir una.")
        return None
    STATE.history.append({"role": "user", "content": prompt})
    trim_history()
    messages = [{"role": "system", "content": build_system_message()}] + STATE.history
    info("ChronoCode pensando... (Ctrl+C para cortar)")
    res = _run_providers(providers, messages)
    if res is None:
        STATE.history.pop()
        return None
    STATE.history.append({"role": "assistant", "content": res.text})
    return res


# =====================================================================
#  BLOQUES DE CÓDIGO Y ARCHIVOS
# =====================================================================
BLOCK_RE = re.compile(r"```([^\n`]*)\n(.*?)```", re.DOTALL)


def extract_blocks(text):
    blocks = []
    for m in BLOCK_RE.finditer(text):
        tag = m.group(1).strip()
        if tag.lower().startswith("chronocode:"):
            blocks.append({"path": tag.split(":", 1)[1].strip() or None, "content": m.group(2)})
    return blocks


def show_diff(path, new_content):
    if os.path.isfile(path):
        old = read_file(path) or ""
        diff = list(difflib.unified_diff(
            old.splitlines(), new_content.splitlines(),
            fromfile=f"{path} (actual)", tofile=f"{path} (propuesto)", lineterm="", n=2))
        if not diff:
            warn("(sin cambios respecto al archivo actual)")
            return False
        for line in diff[:120]:
            if line.startswith("+") and not line.startswith("+++"):
                print(c(line, "32"))
            elif line.startswith("-") and not line.startswith("---"):
                print(c(line, "31"))
            else:
                print(line)
        if len(diff) > 120:
            warn(f"... ({len(diff) - 120} líneas más)")
    else:
        info(f"Archivo nuevo ({len(new_content.splitlines())} líneas).")
    return True


def write_file(path, content):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        if os.path.isfile(path):
            shutil.copyfile(path, path + ".bak")
        if not content.endswith("\n"):
            content += "\n"
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        ok(f"Guardado: {path}" + ("  (backup: .bak)" if os.path.isfile(path + ".bak") else ""))
        return True
    except OSError as e:
        err(f"No se pudo escribir '{path}': {e}")
        return False


def handle_file_block(block):
    path = block["path"] or STATE.current_file
    if not path:
        try:
            path = input(c("¿En qué archivo guardo este código? (vacío = omitir): ", "35")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not path:
            return
    show_diff(path, block["content"])
    if ask_yes_no(f"¿Guardar este código en {path}?"):
        if write_file(path, block["content"]):
            STATE.current_file = path


def truncate(text, limit=MAX_OUTPUT_CHARS):
    if len(text) <= limit:
        return text
    return text[:limit // 2] + "\n[... recortado ...]\n" + text[-limit // 2:]


def run_command(cmd):
    cmd = cmd.strip()
    if not cmd:
        return None
    print(c(f"Comando propuesto:\n  $ {cmd}", "33"))
    if not ask_yes_no("¿Ejecutar este comando?"):
        warn("Comando cancelado.")
        return None
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                             encoding="utf-8", errors="replace",
                             timeout=COMMAND_TIMEOUT, cwd=os.getcwd())
        out = (res.stdout or "") + (res.stderr or "")
        print(out.rstrip() if out.strip() else c("(sin salida)", "90"))
        (ok if res.returncode == 0 else err)(f"[código de salida: {res.returncode}]")
        return f"$ {cmd}\n{out}\n[exit {res.returncode}]"
    except subprocess.TimeoutExpired:
        err(f"El comando superó {COMMAND_TIMEOUT}s y fue detenido.")
        return f"$ {cmd}\n[timeout tras {COMMAND_TIMEOUT}s]"
    except KeyboardInterrupt:
        warn("Comando interrumpido.")
        return None
    except OSError as e:
        err(f"No se pudo ejecutar: {e}")
        return None


def ask_model(user_text):
    res = get_llm_response(user_text)
    if res is None:
        return
    if not res.complete:
        warn("(Respuesta incompleta: solo se procesan bloques de código completos)")
    for block in extract_blocks(res.text):
        handle_file_block(block)


# =====================================================================
#  CLAVES Y ASISTENTE DE PRIMER INICIO
# =====================================================================
def guardar_en_env(variable, valor):
    lines = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines(keepends=True)
    lines = [l for l in lines if not l.startswith(variable + "=")]
    lines.append(f'{variable}="{valor}"\n')
    ENV_PATH.write_text("".join(lines), encoding="utf-8")
    try:
        os.chmod(ENV_PATH, 0o600)   # solo tu usuario puede leerlo
    except OSError:
        pass
    os.environ[variable] = valor


def detectar_proveedor(key):
    if key.startswith("gsk_"):
        return "Groq"
    if key.startswith("sk-or-v1-"):    # antes que "sk-ant-" y "sk-"
        return "OpenRouter"
    if key.startswith("sk-ant-"):      # antes que "sk-"
        return "Anthropic"
    if key.startswith("sk-"):
        return "OpenAI"
    if key.startswith("AIza"):
        return "Gemini"
    return None


def pedir_clave():
    """Pide una API Key, detecta el proveedor y la guarda. Devuelve True si se guardó."""
    print("Pega tu API Key (Gemini, Groq, OpenRouter, OpenAI o Anthropic):")
    try:
        key = input(c("> ", "1;32")).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if not key:
        err("No ingresaste ninguna clave.")
        return False
    prov = detectar_proveedor(key)
    if not prov:
        warn("No reconozco el prefijo de esa clave.")
        try:
            resp = input("¿De qué proveedor es? (gemini/groq/openrouter/openai/anthropic): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return False
        prov = next((n for n in KEY_VARS if n.lower() == resp), None)
        if not prov:
            err("Proveedor no válido.")
            return False
    guardar_en_env(KEY_VARS[prov], key)
    ok(f"Clave de {prov} guardada en {ENV_PATH}\n")
    return True


def setup_wizard():
    if available_providers():
        return
    print(c("=" * 60, "36"))
    print(c("  ¡Bienvenido a ChronoCode!", "1;36"))
    print(c("  Agente 100% Open Source. Trae tu propia API Key (BYOK).", "36"))
    print(c("  Gemini:     https://aistudio.google.com/apikey", "33"))
    print(c("  Groq:       https://console.groq.com/keys", "33"))
    print(c("  OpenRouter: https://openrouter.ai/keys", "33"))
    print(c("=" * 60, "36"))
    if not pedir_clave():
        sys.exit(1)


def mostrar_banner():
    cian, verde, reset = "\033[1;36m", "\033[1;32m", "\033[0m"
    print(f"""
{cian} ██████╗██╗  ██╗██████╗  ██████╗ ███╗   ██╗ ██████╗
██╔════╝██║  ██║██╔══██╗██╔═══██╗████╗  ██║██╔═══██╗
██║     ███████║██████╔╝██║   ██║██╔██╗ ██║██║   ██║
██║     ██╔══██║██╔══██╗██║   ██║██║╚██╗██║██║   ██║
╚██████╗██║  ██║██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ {reset}
               {verde}⚡ v1.0 - Terminal AI Agent ⚡{reset}
""")


HELP = """Comandos:
  /file RUTA   Cambia el archivo de contexto
  /run CMD     Ejecuta un comando (con confirmación)   (atajo: !CMD)
  /key         Añade o cambia una API Key
  /stream      Activa/desactiva el streaming
  /clear       Borra el historial
  /help        Esta ayuda
  /exit        Salir
Cualquier otro texto se envía a la IA."""


def main():
    global STREAM
    setup_wizard()
    load_dotenv(ENV_PATH, override=True)

    mostrar_banner()
    print(f"Proveedores: {' > '.join(p['name'] for p in available_providers())}  |  "
          f"Streaming: {'ON' if STREAM else 'OFF'}")
    print("Escribe /help para ver los comandos.\n")

    if len(sys.argv) > 1:
        set_context_file(" ".join(sys.argv[1:]))

    while True:
        try:
            line = input(c("\n> ", "1;32")).strip()
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print("\n(Usa /exit para salir)")
            continue
        if not line:
            continue

        low = line.lower()
        if low in ("/exit", "/quit", "exit", "salir"):
            print("¡Hasta luego!")
            break
        if low == "/help":
            print(HELP)
        elif low == "/key":
            pedir_clave()
        elif low == "/stream":
            STREAM = not STREAM
            ok("Streaming " + ("activado" if STREAM else "desactivado") + ".")
        elif low == "/clear":
            STATE.history.clear()
            ok("Historial borrado.")
        elif low.startswith("/file"):
            arg = line[5:].strip()
            if arg:
                set_context_file(arg)
            else:
                print(f"Archivo actual: {STATE.current_file or '(ninguno)'}")
        elif low.startswith("/run ") or line.startswith("!"):
            cmd = line[5:] if low.startswith("/run ") else line[1:]
            out = run_command(cmd)
            if out:
                STATE.history.append(
                    {"role": "user", "content": "Salida del comando que ejecuté:\n" + truncate(out)})
        else:
            try:
                ask_model(line)
            except KeyboardInterrupt:
                warn("\nOperación cancelada.")
            except Exception as e:
                err(f"Error inesperado: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
