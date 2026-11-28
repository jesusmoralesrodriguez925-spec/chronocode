<div align="center">

<img src="assets/chronocode.png" alt="ChronoCode" width="320">

# ChronoCode

**Un agente de programación con IA para tu terminal, de código abierto.**

[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-22c55e.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776ab.svg)](https://www.python.org/)
[![Plataforma](https://img.shields.io/badge/probado-Termux%20(Android)-22c55e.svg)](#instalación)

[Canal de Telegram](https://t.me/chronocode_dv) · [X](https://x.com/chronocodedv) · [Reportar un problema](https://github.com/jesusmoralesrodriguez925-spec/chronocode/issues)

</div>

ChronoCode lee tu proyecto, crea y edita archivos, ejecuta comandos y pruebas, y te pide confirmación antes de cada acción que modifique algo. Recuerda lo que le pidas que recuerde. Trae tu propia API Key (BYOK): tus claves y tu código solo se envían al proveedor de IA que elijas.

> **Estado:** probado en Termux (Android) con Groq y Gemini. Los demás proveedores están registrados y se probarán con clave real. Windows, macOS y Linux no están verificados.

## Instalación

**Requisitos:** Python 3 y `git`.

```bash
pkg install -y python git bc
git clone --depth 1 https://github.com/jesusmoralesrodriguez925-spec/chronocode.git
cd chronocode
pip install -r requirements.txt
python3 chronocode.py
```

La primera vez, ChronoCode te pide una API Key: eliges el proveedor, pegas la clave y se guarda sola en `.env`. No necesitas crear ni editar archivos.

Para abrirlo con un solo comando:

```bash
echo "alias chronocode='python3 $HOME/chronocode/chronocode.py'" >> ~/.bashrc
source ~/.bashrc
chronocode
```

## Proveedores de IA

| Proveedor | Variable en `.env` | Estado |
|---|---|---|
| Groq | `GROQ_API_KEY` | Probado con herramientas |
| Gemini | `GEMINI_API_KEY` | Probado con herramientas |
| Anthropic | `ANTHROPIC_API_KEY` | Conversión de herramientas probada; llamada real pendiente de clave |
| OpenRouter | `OPENROUTER_API_KEY` | Pendiente de prueba con clave |
| OpenAI | `OPENAI_API_KEY` | Pendiente de prueba con clave |
| DeepSeek | `DEEPSEEK_API_KEY` | Pendiente de prueba con clave |
| Mistral AI | `MISTRAL_API_KEY` | Pendiente de prueba con clave |
| Perplexity | `PERPLEXITY_API_KEY` | Pendiente de prueba con clave |
| Grok (xAI) | `XAI_API_KEY` | Pendiente de prueba con clave |
| Hugging Face | `HUGGINGFACE_API_KEY` | Pendiente de prueba con clave |
| Meta AI | `LLAMA_API_KEY` | Pendiente de prueba con clave |

El agente usa los proveedores en el orden de la tabla. Si uno falla, pasa al siguiente. Si ves un aviso como "límite de uso" o "sin conexión", el agente te dice qué pasó y sigue con el siguiente.

## Comandos

Escribe `/` para ver el menú. Al seguir escribiendo, se filtra. Con Enter ejecutas el comando resaltado, o lo completas si necesita un argumento.

| Comando | Qué hace |
|---|---|
| `/help` | Muestra los comandos |
| `/clear` | Borra la conversación y deja solo el banner |
| `/exit` | Sale del agente |
| `/file RUTA` | Carga un archivo en el contexto, con colores |
| `/run CMD` | Ejecuta un comando de terminal (pide confirmación) |
| `/plan TAREA` | Propone un plan sin ejecutar nada; solo si lo apruebas, lo lleva a cabo |
| `/remember TEXTO` | Guarda algo en tu memoria a largo plazo |
| `/memory` | Muestra tu memoria a largo plazo |
| `/key` | Añade o cambia una API Key |
| `/proveedores` | Muestra los proveedores y cuáles tienen clave |
| `/context` | Muestra cuánto espacio usa la conversación |
| `/compact` | Resume la conversación para liberar espacio |
| `/diff` | Muestra los cambios de git con colores |
| `/rewind` | Deshace el último cambio hecho por el agente |

Cualquier otro texto se envía al agente. Por ejemplo: `crea un archivo prueba.py con un print de hola`.

## Herramientas del agente

| Herramienta | Qué hace | ¿Pide confirmación? |
|---|---|---|
| `Read` | Lee un archivo completo | No |
| `Write` | Crea un archivo nuevo desde cero | Sí, muestra el contenido con colores |
| `Edit` | Cambia solo una parte de un archivo, sin borrar lo demás | Sí, muestra el cambio |
| `Bash` | Ejecuta un comando de Termux | Sí, después de la denylist |
| `Glob` | Busca archivos por nombre o patrón | No |
| `Grep` | Busca texto dentro de los archivos, con número de línea | No |
| `run_tests` | Detecta y ejecuta las pruebas del proyecto | Sí, como cualquier comando |

## Memoria a largo plazo

ChronoCode guarda lo que le pidas recordar en un archivo `Chrono.md` en tu carpeta personal. Se lee al empezar cada conversación.

```
/remember mi lenguaje favorito es Python
/memory
```

Lo puedes revisar o editar cuando quieras con cualquier editor de texto.

## Seguridad

- **Carpeta de trabajo:** el agente solo escribe dentro de la carpeta desde la que lo abriste.
- **Archivos sensibles:** no escribe en `.env`, `.ssh`, `.git`, `.netrc`, `.aws` ni `.gnupg`.
- **Denylist de comandos:** bloquea comandos destructivos o de sistema, como `rm -rf /`, `mkfs`, `dd` sobre discos, `shutdown`, `sudo` y descargas que se ejecutan directamente con `curl | sh`.
- **Peticiones no permitidas:** el agente las rechaza antes de llamar al modelo (malware, robo de cuentas o contraseñas, ataques a sistemas de terceros, fraude).
- **Confirmación:** ningún archivo se escribe ni ningún comando se ejecuta sin tu respuesta `s`.
- **Claves:** `.env` se crea con permisos solo para tu usuario, y las claves no se muestran en pantalla.

Estas capas reducen el riesgo, pero no sustituyen tu criterio: lee cada cambio y cada comando antes de aceptarlo.

## Control de la conversación

- **Esc** o **Ctrl+C** cancelan la respuesta en curso.
- **Dos Esc seguidos** (con el prompt vacío) salen del agente.
- **Ctrl+C** en el prompt no sale: te recuerda usar `/exit`.

## Límites conocidos

- **Límites de uso de los proveedores:** los planes gratuitos devuelven límites por minuto o por día. El agente lo indica y pasa al siguiente proveedor.
- **Archivos grandes:** `Read` envía al modelo los primeros 8 000 caracteres; el agente lo indica.
- **Conexiones lentas:** las peticiones con varias herramientas pueden tardar con una red inestable.

## Pendiente

- Probar los proveedores que aún no tienen clave de prueba.
- Verificar Windows, macOS y Linux.

## Versión anterior

La versión 1 ya no está en `main`. Está guardada en el tag `respaldo-v1-completa`:

```bash
git checkout respaldo-v1-completa
```

## Estructura del proyecto

```
chronocode/
├── assets/
│   └── chronocode.png     # logo del README
├── chronocode.py          # agente (versión principal)
├── install.sh             # crea el comando `chronocode`
├── requirements.txt       # dependencias
├── .env.example           # plantilla de claves, sin valores reales
├── .github/workflows/     # comprobación de sintaxis en cada cambio
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── SECURITY.md
└── README.md
```

## Apoya el proyecto

Si ChronoCode te resulta útil, puedes contribuir con una donación en USDT:

- **Red:** BNB Smart Chain (BEP20)
- **Dirección:** `0xe10D30B2914B49d28C8a4BE47e10D9FF61dbeE83`

Envía únicamente USDT por la red BEP20. Otras redes pueden provocar la pérdida de los fondos.

## Licencia

Distribuido bajo licencia MIT. Las contribuciones son bienvenidas: abre un issue o un pull request.
