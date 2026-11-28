#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChronoCode v2 - Núcleo: bucle agéntico con herramientas y BYOK. Solo Termux por ahora.
Dependencias: requests, python-dotenv.
"""
import getpass
import glob as _glob
import json
import os
import re
import time
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
from rich.syntax import Syntax
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
    {"nombre": "Anthropic", "env": "ANTHROPIC_API_KEY",
     "url": "https://api.anthropic.com/v1/messages",
     "modelo": "claude-haiku-5-5", "tipo": "anthropic"},
    {"nombre": "Mistral AI", "env": "MISTRAL_API_KEY", "url": "https://api.mistral.ai/v1/chat/completions",
     "modelo": "mistral-large-latest"},
    {"nombre": "Perplexity", "env": "PERPLEXITY_API_KEY", "url": "https://api.perplexity.ai/chat/completions",
     "modelo": "sonar"},
    {"nombre": "Grok (xAI)", "env": "XAI_API_KEY", "url": "https://api.x.ai/v1/chat/completions",
     "modelo": "grok-3-mini"},
    {"nombre": "Hugging Face", "env": "HUGGINGFACE_API_KEY", "url": "https://router.huggingface.co/v1/chat/completions",
     "modelo": "Qwen/Qwen2.5-Coder-32B-Instruct"},
    {"nombre": "Meta AI", "env": "LLAMA_API_KEY", "url": "https://api.llama.com/compat/v1/chat/completions",
     "modelo": "Llama-3.3-70B-Instruct"},
]

MAX_PASOS = 10              # pasos de herramientas por petición
EXTENSION_A_LENGUAJE = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".jsx": "jsx", ".tsx": "tsx",
    ".html": "html", ".css": "css", ".json": "json", ".md": "markdown", ".sh": "bash",
    ".bash": "bash", ".yml": "yaml", ".yaml": "yaml", ".toml": "toml", ".ini": "ini",
    ".java": "java", ".kt": "kotlin", ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
    ".cs": "csharp", ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php", ".swift": "swift",
    ".sql": "sql", ".xml": "xml", ".lua": "lua", ".r": "r", ".dart": "dart", ".vue": "vue",
}


def detectar_lenguaje(codigo):
    """Sin adivinar: un bloque sin lenguaje indicado se muestra como texto plano."""
    return "text"


def marcar_bloques_sin_lenguaje(texto):
    """Normaliza los bloques de código para que se resalten bien y no queden marcas sueltas."""
    texto = re.sub(r"^[ \t]+```", "```", texto, flags=re.M)
    texto = re.sub(r"^[ \t]*```[ \t]*(\w+)[ \t]*$", lambda m: "```" + m.group(1).lower(), texto, flags=re.M)
    texto = re.sub(r"^```text[ \t]*$", "```", texto, flags=re.M)

    def reemplazo(m):
        codigo = m.group(1)
        lenguaje = m.group(0).split("\n", 1)[0][3:].strip()
        if lenguaje in ("", "text"):
            lenguaje = detectar_lenguaje(codigo)
        return "```" + lenguaje + "\n" + codigo + "```"

    texto = re.sub(r"```([\w+-]*)[ \t]*\n(.*?)```", lambda m: reemplazo(
        type("M", (), {"group": lambda self, i: (m.group(0) if i == 0 else (m.group(2) if i == 1 else m.group(1)))})()
    ), texto, flags=re.S)
    return texto


def lenguaje_de(path):
    """Lenguaje para resaltar un archivo según su extensión (texto plano si no se conoce)."""
    return EXTENSION_A_LENGUAJE.get(Path(path).suffix.lower(), "text")


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
    "Cuando muestres código, usa SIEMPRE bloques de Markdown con tres comillas invertidas al inicio "
    "y al final, sin sangría. Indica SIEMPRE el lenguaje real del código (```go, ```php, ```python, ```bash, ```html...), "
    "nunca lo dejes vacío ni pongas text para código. "
    "Nunca escribas el código con sangría ni dejes una marca ``` sin cerrar. "
    "Sé breve: en preguntas simples responde en 2 a 4 frases, sin repetir código "
    "que ya hayas mostrado con una herramienta. "
    "Dentro de tablas no pongas código: usa ejemplos cortos de máximo 20 caracteres. "
    "No ayudes a crear malware, robar cuentas o datos, atacar sistemas de terceros, hacer fraude "
    "ni nada ilegal: si la petición lo es, dilo y no uses herramientas. "
    "Para trabajar en archivos usa las herramientas directamente: no preguntes en texto si "
    "puedes hacerlo, porque la propia herramienta pide la confirmación [s/N]. "
    "Lee un archivo antes de editarlo. "
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


def respaldar(path_str):
    """Guarda la copia del archivo antes de cambiarlo (o anota que era nuevo)."""
    p = Path(path_str).expanduser().resolve()
    BACKUP_DIR.mkdir(exist_ok=True)
    indice = _leer_indice()
    if p.exists():
        destino = BACKUP_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}_{len(indice)}_{p.name}"
        destino.write_bytes(p.read_bytes())
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
            p.unlink(missing_ok=True)
            mensaje = f"Eliminado el archivo que se había creado: {p}"
        else:
            p.write_bytes(Path(ultimo["backup"]).read_bytes())
            mensaje = f"Restaurado: {p}"
    except OSError as e:
        return f"ERROR al restaurar: {e}"
    _guardar_indice(indice)
    return mensaje


MAX_LECTURA = 8000   # caracteres máximos que se envían al modelo por archivo


def read_file(path):
    try:
        texto = Path(path).read_text(encoding="utf-8", errors="replace")
        if len(texto) > MAX_LECTURA:
            return (texto[:MAX_LECTURA]
                    + f"\n\n[... archivo recortado: se muestran {MAX_LECTURA} de {len(texto)} caracteres ...]")
        return texto
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
        respaldar(path)
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
    respaldar(path)
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


MAX_RESULTADOS = 200


def Glob(pattern, root="."):
    """Busca archivos que coincidan con un patrón (por ejemplo **/*.py)."""
    rutas = sorted(_glob.glob(os.path.join(root, pattern), recursive=True))
    rutas = [r for r in rutas if ruta_permitida(r)[0]]
    if not rutas:
        return "Sin coincidencias."
    extra = "" if len(rutas) <= MAX_RESULTADOS else f"\n[... {len(rutas) - MAX_RESULTADOS} más ...]"
    return "\n".join(rutas[:MAX_RESULTADOS]) + extra


def Grep(pattern, path="."):
    """Busca un texto (expresión regular) dentro de los archivos de una carpeta."""
    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"ERROR: expresión regular inválida: {e}"
    base = Path(path).expanduser()
    if not base.exists():
        return f"ERROR: no existe {path}"
    archivos = [base] if base.is_file() else base.rglob("*")
    encontrados = []
    for archivo in archivos:
        if not archivo.is_file() or not ruta_permitida(str(archivo))[0]:
            continue
        if any(parte in {".git", "node_modules", "__pycache__", ".chronocode_backups"} for parte in archivo.parts):
            continue
        try:
            if archivo.stat().st_size > 1_000_000:
                continue
            for n, linea in enumerate(archivo.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if regex.search(linea):
                    encontrados.append(f"{archivo}:{n}: {linea.strip()[:200]}")
                    if len(encontrados) >= MAX_RESULTADOS:
                        return "\n".join(encontrados) + "\n[... resultados truncados ...]"
        except OSError:
            continue
    return "\n".join(encontrados) or "Sin coincidencias."


HERRAMIENTAS = {
    "Read": read_file, "Write": write_file, "Edit": edit_file,
    "Bash": run_command, "run_tests": run_tests,
    "Glob": Glob, "Grep": Grep,
}


def _esquema(nombre, descripcion, props=None, requeridos=None):
    return {"type": "function", "function": {
        "name": nombre, "description": descripcion,
        "parameters": {"type": "object", "properties": props or {}, "required": requeridos or []}}}


ESQUEMAS = [
    _esquema("Read", "Lee un archivo completo. Úsala cuando el usuario pida revisar o mostrar un archivo.",
             {"path": {"type": "string"}}, ["path"]),
    _esquema("Write", "Crea un archivo nuevo desde cero. No la uses para cambiar partes de un archivo existente.",
             {"path": {"type": "string"}, "content": {"type": "string"}}, ["path", "content"]),
    _esquema("Edit", "Cambia solo una parte de un archivo existente (por ejemplo un color o una línea con error). No borra lo demás.",
             {"path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"}},
             ["path", "old_string", "new_string"]),
    _esquema("Glob", "Busca archivos por nombre o patrón, por ejemplo **/*.py. Úsala para encontrar archivos.",
             {"pattern": {"type": "string"}, "root": {"type": "string"}}, ["pattern"]),
    _esquema("Grep", "Busca un texto o expresión regular dentro de los archivos. Úsala para encontrar dónde aparece algo.",
             {"pattern": {"type": "string"}, "path": {"type": "string"}}, ["pattern"]),
    _esquema("Bash", "Ejecuta un comando de Termux como si fuera el usuario: instalar, correr un servidor, listar archivos o ver errores.",
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
    """Devuelve el mensaje del asistente con el mismo formato para todos los proveedores."""
    if prov.get("tipo") == "anthropic":
        return _llamar_anthropic(prov, mensajes)
    return llamar_modelo_openai(prov, mensajes)


def _a_formato_anthropic(mensajes):
    """Convierte el historial (formato OpenAI) al formato de mensajes de Anthropic."""
    system = "\n\n".join(m["content"] for m in mensajes if m["role"] == "system")
    salida = []
    for m in mensajes:
        if m["role"] == "system":
            continue
        if m["role"] == "assistant":
            bloques = []
            if m.get("content"):
                bloques.append({"type": "text", "text": m["content"]})
            for llamada in m.get("tool_calls") or []:
                try:
                    entrada = json.loads(llamada["function"].get("arguments") or "{}")
                except json.JSONDecodeError:
                    entrada = {}
                bloques.append({"type": "tool_use", "id": llamada["id"],
                                "name": llamada["function"]["name"], "input": entrada})
            salida.append({"role": "assistant", "content": bloques or [{"type": "text", "text": "..."}]})
        elif m["role"] == "tool":
            bloque = {"type": "tool_result", "tool_use_id": m["tool_call_id"],
                      "content": m.get("content") or ""}
            ultimo = salida[-1] if salida else None
            if (ultimo and ultimo["role"] == "user" and isinstance(ultimo["content"], list)
                    and ultimo["content"] and ultimo["content"][0].get("type") == "tool_result"):
                ultimo["content"].append(bloque)
            else:
                salida.append({"role": "user", "content": [bloque]})
        else:
            salida.append({"role": "user", "content": m["content"]})
    return system, salida


def _llamar_anthropic(prov, mensajes):
    system, msgs = _a_formato_anthropic(mensajes)
    headers = {"x-api-key": os.getenv(prov["env"]).strip(),
               "anthropic-version": "2023-06-01",
               "Content-Type": "application/json"}
    herramientas = [{"name": e["function"]["name"], "description": e["function"]["description"],
                     "input_schema": e["function"]["parameters"]} for e in ESQUEMAS]
    payload = {"model": prov["modelo"], "max_tokens": 4096, "system": system,
               "messages": msgs, **({} if ESTADO_PLAN["sin_herramientas"] else {"tools": herramientas})}
    r = requests.post(prov["url"], headers=headers, json=payload, timeout=TIMEOUT)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:150]}")
    bloques = r.json().get("content", [])
    texto = "".join(b.get("text", "") for b in bloques if b.get("type") == "text")
    llamadas = [{"id": b["id"], "type": "function",
                 "function": {"name": b["name"], "arguments": json.dumps(b.get("input") or {})}}
                for b in bloques if b.get("type") == "tool_use"]
    return {"content": texto, "tool_calls": llamadas}


def llamar_modelo_openai(prov, mensajes):
    headers = {"Authorization": f"Bearer {os.getenv(prov['env']).strip()}",
               "Content-Type": "application/json"}
    payload = {"model": prov["modelo"], "messages": mensajes}
    if not ESTADO_PLAN["sin_herramientas"]:
        payload["tools"] = ESQUEMAS
        payload["tool_choice"] = "auto"
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
    hechos = []
    for _ in range(MAX_PASOS):
        msg = None
        for prov in provs:
            try:
                msg = llamar_modelo(prov, mensajes)
                break
            except (requests.RequestException, RuntimeError, KeyError) as e:
                print(f"[{prov['nombre']}] no disponible: {str(e)[:120]}. Pruebo el siguiente.")
        if msg is None:
            if hechos:
                resumen = "Acciones completadas antes del fallo:\n" + "\n".join(hechos)
                historial.append({"role": "assistant", "content": resumen})
                return resumen + "\n\nNingún proveedor respondió para terminar. Revisa tu conexión o tus claves."
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
            if resultado.startswith(("BLOQUEADO", "CANCELADO")):
                console.print(Text(f"⛔ {nombre}: {resultado}", style="yellow"))
            hechos.append(f"- {nombre}: {resultado.splitlines()[0][:150] if resultado else ''}")
            mensajes.append({"role": "tool", "tool_call_id": llamada["id"], "content": resultado})
    return "Se alcanzó el límite de pasos para esta petición."


COMANDOS = [
    ("/help", "Muestra los comandos"),
    ("/clear", "Borra el chat"),
    ("/exit", "Sale del agente"),
    ("/file", "Carga un archivo en el contexto"),
    ("/run", "Ejecuta un comando de terminal"),
    ("/key", "Añade o cambia una API Key"),
    ("/proveedores", "Muestra los proveedores y cuáles tienen clave"),
    ("/plan", "Propone un plan y lo ejecuta si lo apruebas"),
    ("/context", "Muestra cuánto espacio usa la conversación"),
    ("/compact", "Resume la conversación para liberar espacio"),
    ("/diff", "Muestra los cambios de git con colores"),
    ("/rewind", "Deshace el último cambio del agente"),
]
ULTIMA = {"texto": ""}
ESTADO_PLAN = {"sin_herramientas": False}
CON_ARGUMENTO = {"/file", "/run", "/plan"}


def _guardar_env(variable, valor):
    env = Path(__file__).resolve().parent / ".env"
    lineas = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    lineas = [l for l in lineas if not l.startswith(variable + "=")]
    lineas.append(f'{variable}="{valor}"')
    env.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    try:
        os.chmod(env, 0o600)
    except OSError:
        pass
    os.environ[variable] = valor


def _pedir_clave():
    print("Proveedores: " + ", ".join(pr["nombre"] for pr in PROVEEDORES))
    nombre = input("Proveedor (nombre exacto de la lista): ").strip()
    prov = next((pr for pr in PROVEEDORES if pr["nombre"].lower() == nombre.lower()), None)
    if prov is None:
        return "Proveedor no válido."
    valor = getpass.getpass(f"Clave de {prov['nombre']} (no se muestra): ").strip()
    if not valor:
        return "No ingresaste ninguna clave."
    _guardar_env(prov["env"], valor)
    return f"Clave de {prov['nombre']} guardada en .env"


def _compactar(historial):
    if len(historial) <= 6:
        return "Hay muy pocos mensajes para compactar."
    provs = proveedores_activos()
    if not provs:
        return "No hay proveedores configurados."
    prov = next((x for x in provs if x.get("tipo") != "anthropic"), None)
    if prov is None:
        return "Para compactar hace falta un proveedor compatible con OpenAI."
    viejos = "\n".join(f"{m['role']}: {m.get('content') or ''}" for m in historial[:-6])
    prompt = ("Resume de forma concisa esta conversación: decisiones, archivos modificados y "
              "pendientes. Responde solo con el resumen.\n\n" + viejos)
    headers = {"Authorization": f"Bearer {os.getenv(prov['env']).strip()}", "Content-Type": "application/json"}
    try:
        r = requests.post(prov["url"], headers=headers, timeout=TIMEOUT,
                          json={"model": prov["modelo"], "messages": [{"role": "user", "content": prompt}]})
        resumen = r.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, ValueError, IndexError) as e:
        return f"No se pudo compactar: {type(e).__name__}"
    historial[:] = [{"role": "user", "content": "Resumen de la conversación anterior:\n" + resumen}] + historial[-6:]
    return "Historial compactado."


def manejar_comando(linea, historial):
    """Procesa los comandos con /. Devuelve True si el comando se atendió."""
    partes = linea.split(maxsplit=1)
    cmd = partes[0].lower()
    arg = partes[1].strip() if len(partes) > 1 else ""

    if cmd == "/file":
        if not arg:
            print("Uso: /file RUTA")
            return True
        p = Path(arg).expanduser()
        if not p.is_file():
            print(f"No existe el archivo: {arg}")
            return True
        contenido = p.read_text(encoding="utf-8", errors="replace")[:MAX_SALIDA * 4]
        historial.append({"role": "user", "content": f"Archivo de contexto ({arg}):\n{contenido}"})
        print(f"Archivo cargado en el contexto: {arg}")
        return True
    if cmd == "/run":
        if not arg:
            print("Uso: /run COMANDO")
            return True
        salida = run_command(arg)
        historial.append({"role": "user", "content": "Salida del comando que ejecuté:\n" + salida[:MAX_SALIDA]})
        print(salida)
        return True
    if cmd == "/key":
        print(_pedir_clave())
        return True
    if cmd == "/proveedores":
        activos = {pr["nombre"] for pr in proveedores_activos()}
        for pr in PROVEEDORES:
            marca = "sí" if pr["nombre"] in activos else "—"
            print(f"  {pr['nombre']:<14} clave: {marca:<3} modelo: {pr['modelo']}")
        return True
    if cmd == "/plan":
        if not arg:
            print("Uso: /plan TAREA (ejemplo: /plan crea una página de inicio en HTML)")
            return True
        if not proveedores_activos():
            print("No hay proveedores configurados.")
            return True
        pedir = ("Haz un plan breve y numerado para esta tarea: qué archivos crearías o editarías, "
                 "qué cambiarías y cómo lo comprobarías. Solo describe el plan, no ejecutes nada.\n\n"
                 "Tarea: " + arg)
        try:
            ESTADO_PLAN["sin_herramientas"] = True
            try:
                plan = responder([{"role": "user", "content": pedir}])
            finally:
                ESTADO_PLAN["sin_herramientas"] = False
        except Exception as e:
            print(f"No se pudo generar el plan: {type(e).__name__}: {str(e)[:120]}")
            return True
        if not plan or not plan.strip() or plan.startswith("Ningún proveedor respondió"):
            print("No se pudo generar el plan. No se hizo ningún cambio.")
            return True
        console.print(Markdown(plan, code_theme="monokai"))
        if not confirmar("¿Aprobar este plan y ejecutarlo?"):
            print("Plan no aprobado. No se hizo ningún cambio.")
            return True
        historial.append({"role": "user",
                          "content": f"Ejecuta este plan aprobado para la tarea: {arg}\n\n{plan}"})
        try:
            respuesta = responder(historial)
        except Exception as e:
            print(f"Error al ejecutar el plan: {type(e).__name__}: {str(e)[:120]}")
            return True
        ULTIMA["texto"] = respuesta
        console.print(Markdown(marcar_bloques_sin_lenguaje(respuesta), code_theme="monokai"))
        return True
    if cmd == "/context":
        usados = len(json.dumps(historial, ensure_ascii=False)) // 4
        limite = 24000
        print(f"Tokens estimados: {usados:,} / {limite:,} ({min(100, usados * 100 // limite)}%)")
        print(f"Mensajes en el historial: {len(historial)}")
        return True
    if cmd == "/compact":
        print(_compactar(historial))
        return True
    if cmd == "/diff":
        try:
            r = subprocess.run(["git", "diff"], capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired) as e:
            print(f"No se pudo ejecutar git: {e}")
            return True
        salida = r.stdout.strip()
        if not salida:
            print("No hay cambios sin confirmar.")
        else:
            console.print(Syntax(salida[:20000], "diff", theme="ansi_dark", word_wrap=True))
        return True
    if cmd == "/rewind":
        print(rewind())
        return True
    return False

def _teclas_menu():
    """Enter: si el menú está abierto, aplica el comando resaltado y lo ejecuta."""
    from prompt_toolkit.key_binding import KeyBindings
    teclas = KeyBindings()

    @teclas.add("enter")
    def _(event):
        buf = event.current_buffer
        estado = buf.complete_state
        if estado is not None and estado.completions:
            comp = estado.current_completion or estado.completions[0]
            buf.apply_completion(comp)
            buf.complete_state = None
            if comp.text.strip() in CON_ARGUMENTO:
                return            # el comando necesita argumento: no se envía
        buf.validate_and_handle()

    return teclas


if PT_OK:
    class ComandosCompleter(Completer):
        """Al escribir "/" muestra el menú y lo filtra mientras escribes."""

        def get_completions(self, document, complete_event):
            texto = document.text_before_cursor
            if not texto.startswith("/") or " " in texto:
                return
            for cmd, desc in COMANDOS:
                if cmd.startswith(texto):
                    yield Completion(cmd + (" " if cmd in CON_ARGUMENTO else ""), start_position=-len(texto), display_meta=desc)

    _sesion = PromptSession(completer=ComandosCompleter(), complete_while_typing=True, key_bindings=_teclas_menu())


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
        if linea.startswith("/"):
            if not manejar_comando(linea, historial):
                console.print(Text("Comando desconocido. Escribe /help para ver los comandos.",
                                   style="yellow"))
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
        respuesta = None
        try:
            respuesta = responder(historial)
        except KeyboardInterrupt:
            console.print(Text("Petición cancelada.", style="yellow"))
        except Exception as e:
            console.print(Text(f"Error inesperado: {type(e).__name__}: {str(e)[:150]}", style="red"))
        finally:
            estado.stop()
            ESTADO_SPINNER["activo"] = None
        if respuesta is None:
            continue
        ULTIMA["texto"] = respuesta
        console.print(Markdown(marcar_bloques_sin_lenguaje(respuesta), code_theme="monokai"))


if __name__ == "__main__":
    main()
