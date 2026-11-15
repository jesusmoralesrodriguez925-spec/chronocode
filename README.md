# ChronoCode


![Screenshot_20261114-204339_Termux.jpg](https://github.com/user-attachments/assets/314b91e3-b595-4271-b037-7ec99d1a4703)


**ES:** Agente de IA de código abierto para tu terminal. Sin servidores, sin cuentas, sin pagos: tú pones tu propia API Key (BYOK) y todo corre en tu equipo.
**EN:** Open-source AI coding agent for your terminal. No servers, no accounts, no payments: you bring your own API key (BYOK) and everything runs on your machine.

Funciona en / Works on: Android (Termux), Linux, macOS, Windows.

---

## Español

### ¿Qué es BYOK?
*Bring Your Own Key*: usas tu propia API Key de un proveedor de IA. ChronoCode habla directamente con el proveedor; no existe ningún servidor intermedio y tu clave solo se guarda en un archivo `.env` local.

### Proveedores soportados
Gemini, Groq, OpenAI y Anthropic. Si uno falla (límite de uso, clave inválida, timeout, servicio no disponible en tu región), ChronoCode pasa automáticamente al siguiente que tengas configurado. Usa solo los proveedores disponibles en tu país y respeta sus términos de uso.

### Instalación rápida (Termux, Linux, macOS)
```bash
git clone https://github.com/TU_USUARIO/chronocode.git
cd chronocode
bash install.sh
python chronocode.py
```

### Instalación manual
```bash
pip install requests python-dotenv
python chronocode.py
```
En Windows: instala Python desde python.org (marca "Add Python to PATH"), luego `pip install requests python-dotenv` y `python chronocode.py`.

### Cómo conseguir una API Key gratis
- **Gemini:** https://aistudio.google.com/apikey (capa gratuita con límites diarios).
- **Groq:** https://console.groq.com/keys (capa gratuita con límites por minuto).

Al primer inicio, ChronoCode te pide la clave, detecta el proveedor por su prefijo (`AIza`, `gsk_`, `sk-ant-`, `sk-`) y la guarda en `.env`. Puedes añadir otra con `/key`.

### Uso
```bash
python chronocode.py              # modo conversación
python chronocode.py mi_script.py # con un archivo como contexto
```

| Comando | Acción |
|---|---|
| `/file RUTA` | Cambia el archivo de contexto |
| `/run CMD` o `!CMD` | Ejecuta un comando (pide confirmación) |
| `/key` | Añade o cambia una API Key |
| `/stream` | Activa/desactiva el streaming |
| `/clear` | Borra el historial |
| `/exit` | Sale |

### Configuración opcional (`.env`)
```
GEMINI_API_KEY="AIza..."
GROQ_API_KEY="gsk_..."
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."

CHRONO_PROVIDER_ORDER="gemini,groq"   # orden de preferencia
CHRONO_CONNECT_TIMEOUT=20             # segundos para conectar
CHRONO_READ_TIMEOUT=120               # segundos esperando respuesta
GEMINI_MODEL="gemini-flash-latest"    # los modelos se pueden cambiar sin tocar el código
```

### Seguridad
- Nunca subas tu `.env` a GitHub. Este repo lo ignora en `.gitignore`.
- ChronoCode siempre pide confirmación antes de guardar archivos o ejecutar comandos. Léelos antes de aceptar.
- El contenido de tus archivos y conversaciones se envía al proveedor que uses; revisa su política de privacidad.

---

## English

### What is BYOK?
*Bring Your Own Key*: you use your own API key from an AI provider. ChronoCode talks directly to the provider. There is no middle server, and your key is stored only in a local `.env` file.

### Supported providers
Gemini, Groq, OpenAI and Anthropic. If one fails (rate limit, invalid key, timeout, service unavailable in your region), ChronoCode automatically falls back to the next configured one. Use only providers available in your country and follow their terms of service.

### Quick install (Termux, Linux, macOS)
```bash
git clone https://github.com/YOUR_USER/chronocode.git
cd chronocode
bash install.sh
python chronocode.py
```

### Manual install
```bash
pip install requests python-dotenv
python chronocode.py
```
On Windows: install Python from python.org (check "Add Python to PATH"), then `pip install requests python-dotenv` and `python chronocode.py`.

### Getting a free API key
- **Gemini:** https://aistudio.google.com/apikey (free tier with daily limits).
- **Groq:** https://console.groq.com/keys (free tier with per-minute limits).

On first run, ChronoCode asks for your key, detects the provider from its prefix (`AIza`, `gsk_`, `sk-ant-`, `sk-`) and saves it to `.env`. Add another one anytime with `/key`.

### Usage
```bash
python chronocode.py              # chat mode
python chronocode.py my_script.py # with a file as context
```

| Command | Action |
|---|---|
| `/file PATH` | Change the context file |
| `/run CMD` or `!CMD` | Run a command (asks for confirmation) |
| `/key` | Add or change an API key |
| `/stream` | Toggle streaming |
| `/clear` | Clear history |
| `/exit` | Quit |

### Security
- Never commit your `.env` to GitHub (it is listed in `.gitignore`).
- ChronoCode always asks for confirmation before writing files or running commands. Read them before accepting.
- Your files and conversations are sent to the provider you use; check their privacy policy.

---

## License
MIT. Contributions welcome.
