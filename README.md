<div align="center">

<img src="assets/chronocode.png" alt="ChronoCode" width="320">

# ChronoCode

**Un agente de programación con IA para tu terminal, de código abierto.**

[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-22c55e.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776ab.svg)](https://www.python.org/)
[![Plataforma](https://img.shields.io/badge/plataforma-Termux%20(Android)-22c55e.svg)](#instalación)

[Canal de Telegram](https://t.me/chronocode_dv) · [X](https://x.com/chronocodedv) · [Reportar un problema](https://github.com/jesusmoralesrodriguez925-spec/chronocode/issues)

</div>

ChronoCode lee tu proyecto, propone cambios, crea y edita archivos, ejecuta pruebas y comandos, y te pide confirmación antes de cada acción que modifique algo. Trae tu propia API Key (BYOK): tus claves y tu código solo se envían al proveedor de IA que elijas.

> **Estado:** versión 2, en uso. Hoy se prueba sobre todo en Termux (Android). Windows, macOS y Linux no están verificados en esta versión.

## Qué hace

- **Conversación con formato:** las respuestas salen con títulos, negritas, tablas y bloques de código con colores.
- **Herramientas de trabajo:** el agente puede leer archivos, crearlos, editarlos, ejecutar comandos y correr las pruebas de tu proyecto.
- **Confirmación obligatoria:** cada escritura o comando muestra lo que va a hacer y pide `[s/N]`. Por defecto la respuesta es no.
- **Copias de seguridad:** la versión anterior de cada archivo se guarda antes de cambiarlo.
- **Seguridad:** rutas limitadas a la carpeta de trabajo, denylist de comandos destructivos y rechazo de peticiones ilegales.

## Instalación

**Requisitos:** Python 3 y `git` en Termux.

```bash
pkg install -y python git bc
git clone https://github.com/jesusmoralesrodriguez925-spec/chronocode.git
cd chronocode
pip install requests python-dotenv rich prompt_toolkit
```

Crea tu archivo de claves (solo en tu equipo, nunca lo subas al repo):

```bash
cp .env.example .env
```

Edita `.env` y pon al menos una clave, por ejemplo:

```env
GROQ_API_KEY="gsk_..."
```

Para abrir el agente desde cualquier carpeta, agrega un alias en `~/.bashrc`:

```bash
echo "alias chronocode='python3 $HOME/chronocode/chronocode_v2.py'" >> ~/.bashrc
source ~/.bashrc
```

Luego ejecuta `chronocode`. Debe aparecer el banner con la mascota y los proveedores que tengas configurados.

## Proveedores de IA

La versión 2 usa estos proveedores, en este orden. Si uno falla, prueba el siguiente:

| Proveedor | Variable en `.env` | Dónde obtener la clave |
|---|---|---|
| Groq | `GROQ_API_KEY` | [console.groq.com/keys](https://console.groq.com/keys) |
| OpenRouter | `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| OpenAI | `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| Gemini | `GEMINI_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| DeepSeek | `DEEPSEEK_API_KEY` | [platform.deepseek.com](https://platform.deepseek.com) |

Los planes gratuitos tienen límites de uso. Si ves `HTTP 429`, espera un momento o usa otro proveedor.

## Comandos

| Comando | Qué hace |
|---|---|
| `/help` | Muestra la lista de comandos |
| `/clear` | Borra el historial de la conversación |
| `/exit` | Sale del agente |

Escribe `/` para ver el menú con filtrado. Cualquier otro texto se envía al agente.

## Herramientas del agente

Cuando el modelo lo necesita, usa estas herramientas en varios pasos para completar una tarea:

| Herramienta | Qué hace | ¿Pide confirmación? |
|---|---|---|
| `read_file` | Lee un archivo | No |
| `write_file` | Crea o reemplaza un archivo | Sí, muestra el contenido antes |
| `edit_file` | Cambia un texto exacto (debe aparecer una sola vez) | Sí, muestra el cambio antes |
| `run_command` | Ejecuta un comando de terminal | Sí, después de la denylist |
| `run_tests` | Detecta y ejecuta las pruebas del proyecto | Sí, como cualquier comando |

Ejemplos de peticiones:
- `crea un script que sume dos números desde la terminal`
- `en suma.sh cambia la validación para que acepte letras`
- `ejecuta las pruebas del proyecto`

## Seguridad

- **Carpeta de trabajo:** el agente solo escribe dentro de la carpeta desde la que lo abriste. Las rutas fuera de ella se bloquean y aparece un aviso `⛔` en pantalla.
- **Archivos sensibles:** no escribe en `.env`, `.ssh`, `.git`, `.netrc`, `.aws` ni `.gnupg`.
- **Denylist de comandos:** bloquea comandos destructivos o de sistema, por ejemplo `rm -rf /`, `mkfs`, `dd` sobre discos, `shutdown`, `sudo`, descargas que se ejecutan directamente con `curl | sh`, y bombas de procesos.
- **Peticiones no permitidas:** el agente rechaza antes de llamar al modelo las peticiones sobre malware, robo de cuentas o contraseñas, ataques a sistemas de terceros, fraude y similares.
- **Confirmación:** ningún archivo se escribe ni ningún comando se ejecuta sin tu respuesta `s`.

Estas capas reducen el riesgo, pero no sustituyen tu criterio. Lee cada cambio y cada comando antes de aceptarlo.

## Pendiente (próximas versiones)

Lo que todavía no está en la versión 2:

- **Respuestas largas** para peticiones simples: el modelo tiende a explicar de más.
- **Tablas en pantallas estrechas:** las columnas pueden cortarse en un teléfono.
- **Latencia:** las peticiones con varias herramientas pueden tardar.
- **Más proveedores:** Anthropic, Mistral, Cohere, Perplexity, Hugging Face, Meta AI y Grok aún no están en esta versión.
- **Comandos de la versión anterior:** `/file`, `/run`, `/key`, `/proveedores`, `/ver`, `/context`, `/compact`, `/diff` y `/rewind` no están en la versión 2.
- **Otras plataformas:** Windows, macOS y Linux no están probados en esta versión.

## Versión anterior

La versión 1 con los comandos completos quedó guardada en el tag `respaldo-v1-antes-de-v2`. Para verla:

```bash
git checkout respaldo-v1-antes-de-v2
```

## Estructura del proyecto

```
chronocode/
├── assets/
│   └── chronocode.png     # logo del README
├── chronocode_v2.py       # agente (versión actual)
├── legacy/                # versión 1 (respaldo, no se usa)
├── .env.example           # plantilla de claves, sin valores reales
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── SECURITY.md
├── README.md
└── requirements.txt
```

## Apoya el proyecto

Si ChronoCode te resulta útil, puedes contribuir con una donación en USDT:

- **Red:** BNB Smart Chain (BEP20)
- **Dirección:** `0xe10D30B2914B49d28C8a4BE47e10D9FF61dbeE83`

Envía únicamente USDT por la red BEP20. Otras redes pueden provocar la pérdida de los fondos.

## Licencia

Distribuido bajo licencia MIT. Las contribuciones son bienvenidas: abre un issue o un pull request.

## Versión anterior

La versión 1 de ChronoCode está en la carpeta legacy/. La versión actual es chronocode_v2.py.
