<div align="center">

<img src="assets/chronocode.png" alt="ChronoCode" width="320">

# ChronoCode

**El agente de IA de código abierto que corre en tu terminal.**

[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-22c55e.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776ab.svg)](https://www.python.org/)
[![Plataformas](https://img.shields.io/badge/plataformas-Termux%20%7C%20Windows%20%7C%20macOS%20%7C%20Linux-22c55e.svg)](#instalación)

[Canal de Telegram](https://t.me/chronocode_dv) · [X](https://x.com/chronocodedv) · [Reportar un problema](https://github.com/jesusmoralesrodriguez925-spec/chronocode/issues)

</div>

ChronoCode es un agente de programación para la terminal. Trae tu propia API Key (BYOK), no depende de ningún servidor propio y funciona en Android (Termux), Windows, macOS y Linux. Tus claves y tu código solo se envían al proveedor de IA que elijas.

## Características

- **Conversación en la terminal:** las respuestas salen con formato Markdown y bloques de código resaltados. El historial se desplaza con el dedo o con la rueda, como en cualquier terminal.
- **Banner único:** la mascota y los datos del agente aparecen una vez al abrirlo.
- **Herramientas de trabajo:** el agente puede leer, buscar, crear y editar archivos de tu proyecto, y ejecutar comandos. Cada cambio pide tu confirmación.
- **Copias de seguridad y deshacer:** antes de cada cambio se guarda una copia en `.chronocode_backups/`, y `/rewind` deshace el último cambio.
- **Control del contexto:** `/context` muestra cuánto espacio usa la conversación, y `/compact` la resume cuando se llena.
- **Revisión de cambios:** `/diff` muestra los cambios de git con colores.
- **Seguridad:** cada comando pasa por una denylist de comandos destructivos, una revisión por IA y tu confirmación.
- **Varios proveedores de IA:** Gemini, Groq, OpenRouter, OpenAI, Anthropic, DeepSeek, Grok (xAI), Hugging Face, Meta AI, Mistral AI, Cohere y Perplexity. Si uno falla, el agente usa el siguiente que tengas configurado.

## Instalación

**Requisitos:** Python 3 y `git`.

**1. Clona el repositorio**

```bash
git clone https://github.com/jesusmoralesrodriguez925-spec/chronocode.git
cd chronocode
```

**2. Instala las dependencias**

```bash
pip install requests python-dotenv rich prompt_toolkit
```

En macOS o Linux usa `pip3`.

**3. Crea el comando global**

```bash
bash install.sh
```

**4. Reinicia la terminal** (en Termux, cierra la app desde recientes) y ejecuta desde cualquier carpeta:

```bash
chronocode
```

En el primer inicio te pedirá tu API Key y la guardará en un archivo `.env` local, con permisos solo para tu usuario.

## Obtén una API Key

| Proveedor | Dónde obtenerla | Notas |
|---|---|---|
| Gemini | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Capa gratuita con límites por minuto y por día |
| Groq | [console.groq.com/keys](https://console.groq.com/keys) | Capa gratuita con límites por minuto |
| OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) | Modelos con sufijo `:free` |

Puedes añadir más proveedores en cualquier momento con `/key`.

## Comandos

Escribe `/` para ver el menú con filtrado en tiempo real.

| Comando | Acción |
|---|---|
| `/file RUTA` | Cambia el archivo de contexto |
| `/run CMD` o `!CMD` | Ejecuta un comando (pide confirmación) |
| `/key` | Añade o cambia una API Key |
| `/proveedores` | Muestra los proveedores activos y sus modelos |
| `/ver` | Muestra la última respuesta completa |
| `/context` | Muestra el espacio que usa la conversación |
| `/compact` | Resume la conversación para liberar espacio |
| `/diff` | Muestra los cambios de git con colores |
| `/rewind` | Deshace el último cambio hecho por el agente |
| `/clear` | Borra el historial de la conversación |
| `/help` | Muestra la ayuda |
| `/exit` | Sale del agente |

Cualquier otro texto se envía a la IA. Por ejemplo, escribe `crea un archivo prueba.txt con la frase hola mundo`: el agente muestra el contenido, te pide confirmación y lo guarda solo si aceptas.

## Herramientas del agente

Cuando el proveedor lo permite, el agente puede usar estas herramientas en varios pasos para completar una tarea:

| Herramienta | Qué hace | ¿Pide confirmación? |
|---|---|---|
| `read_file` | Lee un archivo | No |
| `glob` | Busca archivos por patrón | No |
| `grep` | Busca texto dentro de los archivos | No |
| `edit_file` | Cambia un texto exacto dentro de un archivo | Sí, muestra el cambio antes |
| `write_file` | Crea o reemplaza un archivo | Sí, muestra el contenido antes |
| `run_command` | Ejecuta un comando de terminal | Sí, después de la denylist |

Las herramientas funcionan con los proveedores compatibles con la API de OpenAI (Groq, OpenRouter, OpenAI, DeepSeek, Grok, Mistral, Perplexity, Hugging Face, Meta AI, Cohere y Gemini). Con Anthropic, el agente responde en modo conversación, sin herramientas.

## Configuración (`.env`)

```env
GEMINI_API_KEY="AIza..."
GROQ_API_KEY="gsk_..."
OPENROUTER_API_KEY="sk-or-v1-..."
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
DEEPSEEK_API_KEY="..."
XAI_API_KEY="xai-..."
HUGGINGFACE_API_KEY="hf_..."
LLAMA_API_KEY="..."
MISTRAL_API_KEY="..."
COHERE_API_KEY="..."
PERPLEXITY_API_KEY="pplx-..."

# Orden de preferencia de proveedores
CHRONO_PROVIDER_ORDER="gemini,groq"

# Modelos (cámbialos sin tocar el código, p. ej. DEEPSEEK_MODEL)
GEMINI_MODEL="gemini-flash-latest"

# Tiempos de espera en segundos
CHRONO_CONNECT_TIMEOUT=20
CHRONO_READ_TIMEOUT=120

# Confirmar antes de ejecutar comandos (1 = sí, 0 = no)
CHRONO_CONFIRMAR=1

# Pantalla propia tipo vim/nano (1 = activada, 0 = desactivada, predeterminado 0)
CHRONO_ALT=0
```

Las variables `*_API_KEY` no se pasan a los comandos que ejecuta el agente.

## Seguridad

- **Confirmación:** ningún archivo se escribe y ningún comando se ejecuta sin tu aprobación. Con `CHRONO_CONFIRMAR=0` se omite la confirmación de comandos, pero la denylist y la revisión por IA siguen activas.
- **Denylist:** bloquea comandos destructivos o de sistema (por ejemplo `rm -rf /`, `mkfs`, `dd` sobre discos, `shutdown`, `sudo`), incluidos los que intentan esconderse en tuberías, `bash -c` o variables.
- **Revisión por IA:** los comandos que propone el modelo se evalúan antes de mostrarse.
- **Escritura de archivos:** el modelo solo puede escribir dentro del directorio de trabajo, y nunca en archivos sensibles como `.env` o `.ssh`.
- **Copias de seguridad:** cada cambio se respalda antes de aplicarse, y `/rewind` lo deshace.
- **Secretos:** el archivo `.env` y las claves no se envían a los comandos ni se suben al repositorio.

Estas capas reducen el riesgo, pero no sustituyen tu criterio: lee cada comando y cada cambio antes de aceptarlo.

## Cambios retirados y por qué

Algunas funciones de versiones anteriores se quitaron o se desactivaron. Esto es lo que cambió y el motivo:

- **Banner animado con la mascota en movimiento:** se quitó del chat. Mantener la mascota animada dentro de la misma pantalla que el historial hacía que la terminal se redibujara y el scroll con el dedo dejara de funcionar. Ahora el banner aparece una sola vez, como texto.
- **Pantalla propia (tipo vim) por defecto:** se desactivó. En esa pantalla la terminal no guarda historial, así que no se podía subir para leer respuestas anteriores. Sigue disponible con `CHRONO_ALT=1`.
- **Comando `/ui`:** se quitó porque el banner fijo ya no existe.
- **Respuesta en vivo (streaming):** se desactivó. Mostraba el texto sin formato Markdown (con `##` y `**` visibles) y mezclaba la respuesta con el historial. Ahora la respuesta aparece completa y con formato.
- **Lista fija de comandos permitidos:** se reemplazó por la denylist, la revisión por IA y la confirmación. Una lista fija impedía usar comandos de Linux normales, y con estas tres capas puedes ejecutar más comandos sin renunciar al control.
- **Interfaz de pantalla completa con prompt_toolkit (`tui.py`):** se probó, pero no se incluye en el uso normal porque mostraba errores de pantalla en Termux. El archivo no forma parte del proyecto.

## Estructura del proyecto

```
chronocode/
├── .github/workflows/     # comprobación de sintaxis en cada cambio
├── assets/
│   └── chronocode.png     # logo del README
├── agent_loop.py          # bucle agéntico: el modelo pide herramientas y recibe resultados
├── chronocode.py          # agente principal: comandos, banner, respuestas y seguridad
├── context_manager.py     # historial de la conversación y compactación
├── tools.py               # herramientas del agente y copias de seguridad
├── install.sh             # crea el comando global `chronocode`
├── requirements.txt       # dependencias
├── .env.example           # plantilla de configuración sin claves
├── .gitignore             # ignora .env, copias y archivos temporales
├── CONTRIBUTING.md        # cómo contribuir
├── SECURITY.md            # cómo reportar vulnerabilidades
├── LICENSE                # licencia MIT
└── README.md
```

## Apoya el proyecto

Si ChronoCode te resulta útil, puedes contribuir con una donación en USDT:

- **Red:** BNB Smart Chain (BEP20)
- **Dirección:** `0xe10D30B2914B49d28C8a4BE47e10D9FF61dbeE83`

Envía únicamente USDT por la red BEP20. Otras redes pueden provocar la pérdida de los fondos.

## Licencia

Distribuido bajo licencia MIT. Las contribuciones son bienvenidas: abre un issue o un pull request.
