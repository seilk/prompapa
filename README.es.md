<p align="center">
  <img src="assets/prompapa-banner.png" alt="prompapa" width="800" />
</p>

<p align="center">
  <em>Escribe en tu idioma. Pulsa <code>Ctrl+]</code> en <strong>Claude Code / Codex / Opencode</strong>. Míralo convertirse en inglés perfecto.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/install-uv-blueviolet" alt="uv" />
  <img src="https://img.shields.io/badge/translation-Google_Cloud-green" alt="Google Cloud Translation" />
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a> · <a href="README.zh.md">中文</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <a href="README.ru.md">Русский</a>
</p>

## Demostración

<table>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-ko.gif" width="600" />
      <br/>🇰🇷 Coreano
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-jp.gif" width="600" />
      <br/>🇯🇵 Japonés
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-cn.gif" width="600" />
      <br/>🇨🇳 Chino
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-fr.gif" width="600" />
      <br/>🇫🇷 Francés
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-es.gif" width="600" />
      <br/>🇪🇸 Español
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-de.gif" width="600" />
      <br/>🇩🇪 Alemán
    </td>
  </tr>
</table>

<p align="center"><em><strong>Escribe en <em>cualquier idioma</em>. Pulsa <code>Ctrl+]</code> para traducir al inglés. Pulsa <code>Ctrl+Q</code> para deshacer.</strong></em></p>

## Por qué existe esto

El lenguaje no es un contenedor neutral para el pensamiento. Las palabras a las que recurrimos primero, la estructura que imponemos antes de saber qué queremos decir, el instinto que precede a la articulación. Todo esto es nativo. Forzar ese proceso a través de una segunda lengua no solo lo ralentiza. Lo remodela silenciosamente.

Los asistentes de codificación de IA llevan una restricción análoga desde la dirección opuesta. La investigación confirma lo que muchos han intuido: estos modelos exhiben un sesgo estructural hacia el inglés, donde la misma intención expresada en un idioma no inglés produce respuestas mediblemente más débiles [[1]](https://arxiv.org/abs/2504.11833). El sesgo va más allá del vocabulario superficial. Los análisis representacionales de los grandes modelos de razonamiento muestran que sus rutas de razonamiento internas están centradas en el inglés por arquitectura, no solo por los datos de entrenamiento. Independientemente del idioma en que llegue un prompt, el modelo converge hacia un espacio latente con forma inglesa antes de comenzar a razonar [[2]](https://arxiv.org/abs/2601.02996). Separar la representación del lenguaje del sustrato de razonamiento revela el mismo patrón: el motor de razonamiento funciona mejor cuando la capa de lenguaje que se le presenta es el inglés [[3]](https://arxiv.org/abs/2505.15257). La consecuencia no es teórica. En once idiomas y cuatro dominios de tareas, los prompts no ingleses producen una degradación consistente tanto en rendimiento como en robustez [[4]](https://arxiv.org/abs/2505.15935).

Dos mentes con propósitos encontrados. Una que piensa con más claridad en su lengua materna. Otra que razona mejor en inglés.

Prompapa se sitúa entre ellas. Nada más.

### Referencias

1. Gao et al. (2025). *Could Thinking Multilingually Empower LLM Reasoning?* [arXiv:2504.11833](https://arxiv.org/abs/2504.11833)
2. Liu et al. (2026). *Large Reasoning Models Are (Not Yet) Multilingual Latent Reasoners.* [arXiv:2601.02996](https://arxiv.org/abs/2601.02996)
3. Zhao et al. (2025). *When Less Language is More: Language-Reasoning Disentanglement Makes LLMs Better Multilingual Reasoners.* NeurIPS 2025. [arXiv:2505.15257](https://arxiv.org/abs/2505.15257)
4. Hofman et al. (2025). *MAPS: A Multilingual Benchmark for Agent Performance and Security.* EACL 2026. [arXiv:2505.15935](https://arxiv.org/abs/2505.15935)

## Instalación

Requiere [uv](https://docs.astral.sh/uv/). Si aún no lo tienes:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Luego instala prompapa:

```bash
uv tool install git+https://github.com/seilk/prompapa
```

## Configuración inicial

Ejecuta el asistente de incorporación para configurar tu clave API:

```bash
papa onboard
```

Esto configura `~/.config/prompapa/config.toml` con tu clave de API de Google Cloud Translation.

### Obtener una clave API de Google Cloud Translation

> **Nivel gratuito:** Google Cloud Translation API (Basic) ofrece **500.000 caracteres gratuitos al mes**. A partir de ahí, son $20 por millón de caracteres. Un prompt de IA típico tiene entre 100 y 300 caracteres, lo que equivale a unas 1.500–5.000 traducciones al día dentro del nivel gratuito.

1. Ve a [console.cloud.google.com](https://console.cloud.google.com) e inicia sesión.
2. Crea un nuevo proyecto o selecciona uno existente.
3. Ve a **APIs y servicios → Biblioteca**, busca **Cloud Translation API** y haz clic en **Habilitar**.
4. Se te pedirá que actives la facturación. Se requiere una tarjeta de crédito, pero **no se te cobrará dentro del nivel gratuito**. ([Detalles de precios](https://cloud.google.com/translate/pricing))
5. Ve a **APIs y servicios → Credenciales → Crear credenciales → Clave de API**.
6. Copia la clave generada y pégala cuando `papa onboard` te la solicite.

## Uso

```bash
papa claude # for Claude-Code
papa codex # for Codex
papa opencode # for Opencode
```

Tu herramienta se abre exactamente igual que siempre. Dos nuevos atajos de teclado:

| Atajo | Acción |
|--------|--------|
| `Ctrl+]` | Traducir la entrada actual al inglés |
| `Ctrl+Q` | Deshacer la traducción, restaurar el texto original |

## Configuración

`~/.config/prompapa/config.toml`:

```toml
provider = "google"
api_key = "your-gcp-translation-api-key"
target_cmd = ["claude"]
preserve_backticks = true
```

`api_key_env` también es compatible si prefieres mantener la clave en una variable de entorno:

```toml
provider = "google"
api_key_env = "GOOGLE_API_KEY"
target_cmd = ["claude"]
```

### preserve_backticks

Mantiene los tokens envueltos en comillas invertidas sin traducir:

```toml
preserve_backticks = true
```

`` `src/auth.ts` `` se mantiene exactamente igual después de la traducción.

## Cómo funciona

Prompapa bifurca tu CLI objetivo en un **PTY (pseudo-terminal)**, situándose de forma transparente entre tu teclado y el proceso. Cada pulsación de tecla pasa sin cambios hasta que pulsas `Ctrl+]`.

En ese momento:

1. Lee la entrada actual de la pantalla del terminal mediante un rastreador de pantalla `pyte`
2. Lanza una llamada asíncrona a la API de Google Cloud Translation
3. Borra el texto original con retrocesos precisamente contados (sin actualización de pantalla)
4. Inyecta el resultado en inglés mediante pegado entre corchetes

El proceso hijo nunca se detiene. La interfaz nunca se redibuja. El texto simplemente... cambia.

## Desarrollo

```bash
git clone https://github.com/seilk/prompapa
cd prompapa
uv sync
uv run pytest -v
```

Ejecutar localmente sin instalar:

```bash
uv run papa claude
```

## Actualización

```bash
papa update
```

Descarga y reinstala la última versión desde GitHub.

## Desinstalación

```bash
papa uninstall
```

Tu configuración en `~/.config/prompapa/` se conserva. Elimínala manualmente si es necesario.

## TODO
- [ ] Soporte de `opencode`
- [ ] Soporte de traducción vía LLM API (OpenAI, Gemini, Claude, ...)
- [ ] Idioma de destino configurable y ampliado (actualmente solo inglés)
