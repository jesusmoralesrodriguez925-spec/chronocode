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

- **Interfaz de terminal:** banner fijo con una mascota animada que cambia de estado (reposo, pensando, ejecutando, listo).
- **Menú de comandos:** escribe `/` y aparece el menú con filtrado en tiempo real.
- **Entrada de texto fluida:** mensajes largos sin cortes e historial con las flechas.
- **Pantalla propia:** se abre en una pantalla dedicada, como `vim` o `nano`, y al salir devuelve la terminal tal como estaba.
- **Comandos del sistema con control:** el agente puede proponer comandos de tu sistema; cada uno pasa por una denylist, una revisión por IA y tu confirmación antes de ejecutarse.
- **12 proveedores de IA:** Gemini, Groq, OpenRouter, OpenAI, Anthropic, DeepSeek, Grok (xAI), Hugging Face, Meta AI, Mistral AI, Cohere y Perplexity. Si uno falla, usa automáticamente el siguiente que tengas configurado.
- **Permisos en Termux:** solicita el acceso al almacenamiento una sola vez.

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
| Gemini | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Capa gratuita con límites diarios |
| Groq | [console.groq.com/keys](https://console.groq.com/keys) | Capa gratuita con límites por minuto |
| OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) | Modelos con sufijo `:free` |

Puedes añadir más proveedores en cualquier momento con `/key`.

## Comandos

| Comando | Acción |
|---|---|
| `/` | Muestra el menú de comandos |
| `/file RUTA` | Cambia el archivo de contexto |
| `/run CMD` o `!CMD` | Ejecuta un comando (pide confirmación) |
| `/key` | Añade o cambia una API Key |
| `/proveedores` | Muestra los proveedores activos y sus modelos |
| `/ver` | Lee la última respuesta completa con scroll |
| `/ui` | Activa o desactiva el banner fijo |
| `/clear` | Borra el historial de la conversación |
| `/help` | Muestra la ayuda |
| `/exit` | Sale del agente |

Cualquier otro texto se envía a la IA. Por ejemplo, escribe `borra el archivo hola.py`: la IA propone el comando, lo revisa y te pide confirmación antes de ejecutarlo.

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
```

Las variables `*_API_KEY` no se pasan a los comandos que ejecuta el agente.

## Seguridad

- **Confirmación:** ningún comando se ejecuta sin tu aprobación. Con `CHRONO_CONFIRMAR=0` se omite, pero la denylist y la revisión por IA siguen activas.
- **Denylist:** bloquea comandos destructivos o de sistema, incluidos los que intentan esconderse en pipes, `bash -c` o `sudo`.
- **Revisión por IA:** los comandos que propone el modelo se evalúan antes de mostrarse.
- **Escritura de archivos:** el modelo solo puede guardar archivos dentro del directorio de trabajo.
- **Secretos:** el archivo `.env` y las claves no se envían a los comandos ni se suben al repositorio.

Estas capas reducen el riesgo, pero no sustituyen tu criterio: lee cada comando antes de aceptarlo.

## Estructura del proyecto

```
chronocode/
├── assets/
│   └── chronocode.png   # logo del README
├── chronocode.py        # agente (un solo archivo)
├── install.sh           # crea el comando global `chronocode`
├── README.md
└── .gitignore           # incluye .env
```

## Apoya el proyecto

Si ChronoCode te resulta útil, puedes contribuir con una donación en USDT:

- **Red:** BNB Smart Chain (BEP20)
- **Dirección:** `0xe10D30B2914B49d28C8a4BE47e10D9FF61dbeE83`

Envía únicamente USDT por la red BEP20. Otras redes pueden provocar la pérdida de los fondos.

## Licencia

Distribuido bajo licencia MIT. Las contribuciones son bienvenidas: abre un issue o un pull request.
