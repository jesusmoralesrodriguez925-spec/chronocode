# README.md para chronocode

```markdown
# ChronoCode

> **EN:** An open-source AI coding agent for your terminal. Bring your own API key (BYOK), no servers, no accounts. Works on Android (Termux), Windows, macOS and Linux.

**ChronoCode** es un agente de programación con IA para tu terminal. Es de código abierto, funciona con tu propia API Key (BYOK) y no depende de ningún servidor nuestro: tus claves y tu código solo viajan al proveedor que elijas.

## Características

- **UI profesional:** banner fijo con una mascota animada que cambia de estado (reposo, pensando, ejecutando, listo), sin repetir cajas en pantalla.
- **Menú interactivo:** escribe `/` y aparece un menú flotante con todos los comandos. Filtra en tiempo real (`/cl` → `/clear`) y elige con las flechas y Enter.
- **Barra de escritura fluida:** textos largos sin cortes, con historial de entradas usando las flechas.
- **Pantalla limpia:** se abre en una pantalla propia, como vim o nano, y al salir devuelve tu terminal tal como estaba.
- **Ejecución de comandos:** puede ejecutar cualquier comando de Linux o Termux que le pidas, con revisión de seguridad y confirmación antes de cada ejecución.
- **Seguridad:** un sistema de bloqueo impide comandos destructivos, como `rm -rf /`, `mkfs`, `dd` sobre discos, `shutdown`, `sudo` o la lectura de tus claves (`.env`, `~/.ssh`).
- **Permisos en Termux:** en Android pide el acceso al almacenamiento una sola vez.
- **12 proveedores de IA:** Gemini, Groq, OpenRouter, OpenAI, Anthropic, DeepSeek, Grok (xAI), Hugging Face, Meta AI, Mistral AI, Cohere y Perplexity. Si uno falla, pasa automáticamente al siguiente que tengas configurado.
- **Multisistema:** Termux, Windows, macOS y Linux.

## Instalación rápida

1. Clona el repositorio y entra en la carpeta:

   ```bash
   git clone https://github.com/jesusmoralesrodriguez925-spec/chronocode.git
   cd chronocode
   ```

2. Instala las dependencias:

   ```bash
   pip install requests python-dotenv rich prompt_toolkit
   ```

   En macOS o Linux usa `pip3`.

3. Crea el alias global:

   ```bash
   bash install.sh
   ```

4. Cierra la terminal por completo y vuelve a abrirla (en Termux, cierra la app desde recientes).

5. Desde cualquier carpeta, escribe:

   ```bash
   chronocode
   ```

El primer inicio te pide tu API Key y la guarda en un archivo `.env` local, con permisos solo para tu usuario.

## Obtén una API Key gratis

- **Gemini:** https://aistudio.google.com/apikey
- **Groq:** https://console.groq.com/keys
- **OpenRouter:** https://openrouter.ai/keys (modelos con sufijo `:free`)

Puedes añadir más con `/key`. Ver los proveedores activos y sus modelos: `/proveedores`.

## Uso

| Comando | Acción |
|---|---|
| `/` | Muestra el menú de comandos |
| `/file RUTA` | Cambia el archivo de contexto |
| `/run CMD` o `!CMD` | Ejecuta un comando (pide confirmación) |
| `/key` | Añade o cambia una API Key |
| `/proveedores` | Muestra los proveedores y sus modelos |
| `/ver` | Lee la última respuesta completa con scroll |
| `/ui` | Activa o desactiva el banner fijo |
| `/clear` | Borra el historial |
| `/help` | Muestra la ayuda |
| `/exit` | Sale |

Cualquier otro texto se envía a la IA. Por ejemplo: `Borra el archivo hola.py`. La IA propone el comando, lo revisa, y tú confirmas antes de ejecutarlo.

## Configuración opcional (`.env`)

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

# Modelos (se pueden cambiar sin tocar el código, p. ej. DEEPSEEK_MODEL)
GEMINI_MODEL="gemini-flash-latest"

# Tiempos de espera (segundos)
CHRONO_CONNECT_TIMEOUT=20
CHRONO_READ_TIMEOUT=120

# Pedir confirmación antes de ejecutar comandos (1 = sí, 0 = no)
CHRONO_CONFIRMAR=1
```

Nota: las variables de entorno `*_API_KEY` no se pasan a los comandos que ejecuta el agente.

## Seguridad

- **Confirmación obligatoria:** ningún comando se ejecuta sin que lo aceptes (salvo que pongas `CHRONO_CONFIRMAR=0`, y aun así la IA debe aprobarlo).
- **Denylist:** bloquea comandos destructivos y de sistema, incluidos los que se esconden en pipes, `bash -c` o `sudo`.
- **Revisión por IA:** los comandos que propone el modelo se evalúan antes de mostrarse.
- **Sandbox de archivos:** el agente solo guarda archivos dentro del directorio de trabajo.
- **Tus secretos:** el archivo `.env` y las claves no se envían a los comandos ni se guardan en el repositorio.

Estas capas reducen mucho el riesgo, pero no sustituyen tu criterio: lee cada comando antes de aceptarlo.

## Estructura

```
chronocode/
├── chronocode.py   # agente (un solo archivo)
├── install.sh      # crea el alias global `chronocode`
├── README.md
└── .gitignore      # incluye .env
```

## Licencia

MIT. Las contribuciones son bienvenidas.
```
