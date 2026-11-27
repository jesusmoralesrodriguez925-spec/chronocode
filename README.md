<div align="center">

<img src="assets/chronocode.png" alt="ChronoCode" width="320">

# ChronoCode

**Un agente de programación con IA para tu terminal, de código abierto.**

[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-22c55e.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776ab.svg)](https://www.python.org/)
[![Plataforma](https://img.shields.io/badge/probado-Termux%20(Android)-22c55e.svg)](#instalación)

[Canal de Telegram](https://t.me/chronocode_dv) · [X](https://x.com/chronocodedv) · [Reportar un problema](https://github.com/jesusmoralesrodriguez925-spec/chronocode/issues)

</div>

ChronoCode lee tu proyecto, crea y edita archivos, ejecuta comandos y pruebas, y te pide confirmación antes de cada acción que modifique algo. Trae tu propia API Key (BYOK): tus claves y tu código solo se envían al proveedor de IA que elijas.

> **Estado:** probado en Termux (Android) con Groq y Gemini. Los demás proveedores están registrados, pero solo se han probado con su clave real donde se indica. Windows, macOS y Linux no están verificados.

## Qué hace

- **Conversación con formato:** títulos, negritas, tablas y bloques de código con colores.
- **Herramientas:** leer, buscar, crear y editar archivos; ejecutar comandos y pruebas del proyecto.
- **Confirmación obligatoria:** cada escritura o comando muestra lo que va a hacer y pide `[s/N]`. Por defecto, no.
- **Copias de seguridad y deshacer:** la versión anterior de cada archivo se guarda antes de cambiarlo, y `/rewind` la restaura.
- **Seguridad:** rutas limitadas a la carpeta de trabajo, denylist de comandos destructivos y rechazo de peticiones ilegales.

## Instalación

**Requisitos:** Python 3 y `git`.

```bash
pkg install -y python git bc        # en Termux
git clone --depth 1 https://github.com/jesusmoralesrodriguez925-spec/chronocode.git
cd chronocode
pip install -r requirements.txt
cp .env.example .env                # y pon tu API Key dentro
python3 chronocode.py
```

Para abrirlo con un solo comando, agrega un alias:

```bash
echo "alias chronocode='python3 $HOME/chronocode/chronocode.py'" >> ~/.bashrc
source ~/.bashrc
chronocode
```

Edita `.env` y pon al menos una clave, por ejemplo `GROQ_API_KEY="gsk_..."`. Nunca subas `.env` al repositorio.

## Proveedores de IA

| Proveedor | Variable en `.env` | Estado |
|---|---|---|
| Groq | `GROQ_API_KEY` | Probado con herramientas |
| Gemini | `GEMINI_API_KEY` | Probado con herramientas |
| OpenRouter | `OPENROUTER_API_KEY` | Registrado, pendiente de prueba |
| OpenAI | `OPENAI_API_KEY` | Registrado, pendiente de prueba |
| DeepSeek | `DEEPSEEK_API_KEY` | Registrado, pendiente de prueba |
| Anthropic | `ANTHROPIC_API_KEY` | Conversión de herramientas probada; llamada real pendiente de clave |
| Mistral AI | `MISTRAL_API_KEY` | Registrado, pendiente de prueba |
| Perplexity | `PERPLEXITY_API_KEY` | Registrado, pendiente de prueba |
| Cohere | `COHERE_API_KEY` | Registrado, pendiente de prueba |
| Grok (xAI) | `XAI_API_KEY` | Registrado, pendiente de prueba |
| Hugging Face | `HUGGINGFACE_API_KEY` | Registrado, pendiente de prueba |
| Meta AI | `LLAMA_API_KEY` | Registrado, pendiente de prueba |

El agente usa los proveedores en el orden de la tabla. Si uno falla, pasa al siguiente. Los planes gratuitos tienen límites: si ves `HTTP 429`, espera o usa otro proveedor.

Puedes ver cuáles tienen clave con `/proveedores`, y añadir una clave con `/key`.

## Comandos

Escribe `/` para ver el menú con filtrado en tiempo real.

| Comando | Qué hace |
|---|---|
| `/help` | Muestra los comandos |
| `/clear` | Borra el chat |
| `/exit` | Sale del agente |
| `/file RUTA` | Carga un archivo en el contexto |
| `/run CMD` | Ejecuta un comando de terminal (pide confirmación) |
| `/key` | Añade o cambia una API Key |
| `/proveedores` | Muestra los proveedores y cuáles tienen clave |
| `/ver` | Muestra la última respuesta completa |
| `/context` | Muestra cuánto espacio usa la conversación |
| `/compact` | Resume la conversación para liberar espacio |
| `/diff` | Muestra los cambios de git con colores |
| `/rewind` | Deshace el último cambio hecho por el agente |

Cualquier otro texto se envía al agente. Por ejemplo: `crea un archivo prueba.txt con hola`.

## Herramientas del agente

| Herramienta | Qué hace | ¿Pide confirmación? |
|---|---|---|
| `read_file` | Lee un archivo (hasta 8 000 caracteres) | No |
| `write_file` | Crea o reemplaza un archivo | Sí, muestra el contenido antes |
| `edit_file` | Cambia un texto exacto que aparezca una sola vez | Sí, muestra el cambio antes |
| `run_command` | Ejecuta un comando de terminal | Sí, después de la denylist |
| `run_tests` | Detecta y ejecuta las pruebas del proyecto | Sí, como cualquier comando |

## Seguridad

- **Carpeta de trabajo:** el agente solo escribe dentro de la carpeta desde la que lo abriste.
- **Archivos sensibles:** no escribe en `.env`, `.ssh`, `.git`, `.netrc`, `.aws` ni `.gnupg`.
- **Denylist de comandos:** bloquea comandos destructivos o de sistema, como `rm -rf /`, `mkfs`, `dd` sobre discos, `shutdown`, `sudo`, y descargas que se ejecutan directamente con `curl | sh`.
- **Peticiones no permitidas:** el agente las rechaza antes de llamar al modelo (malware, robo de cuentas o contraseñas, ataques a sistemas de terceros, fraude).
- **Confirmación:** ningún archivo se escribe ni ningún comando se ejecuta sin tu respuesta `s`.

Estas capas reducen el riesgo, pero no sustituyen tu criterio: lee cada cambio y cada comando antes de aceptarlo.

## Límites conocidos

- **Límites de uso de los proveedores:** los planes gratuitos devuelven `429` cuando se agota la cuota. No es un error del agente.
- **Archivos grandes:** `read_file` envía solo los primeros 8 000 caracteres al modelo. El agente lo indica, pero el análisis de archivos muy grandes es parcial.
- **Conexiones lentas:** las peticiones con varias herramientas pueden tardar, sobre todo con una red inestable.

## Pendiente

- **Probar los proveedores** que aún no tienen clave de prueba (OpenRouter, OpenAI, DeepSeek, Mistral, Perplexity, Cohere, Grok, Hugging Face, Meta AI y Anthropic).
- **Windows, macOS y Linux:** no están verificados.
- **Respuestas más breves** en preguntas muy simples, en un ajuste futuro.

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
