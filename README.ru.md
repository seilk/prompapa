<p align="center">
  <img src="assets/prompapa-banner.png" alt="prompapa" width="800" />
</p>

<p align="center">
  <em>Пишите на родном языке. Нажмите <code>Ctrl+]</code> в <strong>Claude Code / Codex / Opencode</strong>. Смотрите, как это становится безупречным английским.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/install-uv-blueviolet" alt="uv" />
  <img src="https://img.shields.io/badge/translation-Google_Cloud-green" alt="Google Cloud Translation" />
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a> · <a href="README.zh.md">中文</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <a href="README.ru.md">Русский</a>
</p>

## Демонстрация

<table>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-ko.gif" width="600" />
      <br/>🇰🇷 Корейский
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-jp.gif" width="600" />
      <br/>🇯🇵 Японский
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-cn.gif" width="600" />
      <br/>🇨🇳 Китайский
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-fr.gif" width="600" />
      <br/>🇫🇷 Французский
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-es.gif" width="600" />
      <br/>🇪🇸 Испанский
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-de.gif" width="600" />
      <br/>🇩🇪 Немецкий
    </td>
  </tr>
</table>

<p align="center"><em><strong>Пишите на <em>любом языке</em>. Нажмите <code>Ctrl+]</code> для перевода на английский. Нажмите <code>Ctrl+Q</code> для отмены.</strong></em></p>

## Зачем это нужно

Язык не является нейтральным сосудом для мысли. Слова, к которым мы обращаемся первыми, структура, которую мы навязываем, ещё не понимая, что имеем в виду, инстинкт, предшествующий артикуляции. Всё это родное. Принуждение этого процесса через второй язык не просто замедляет его. Оно тихо переформирует его.

ИИ-ассистенты для программирования несут аналогичное ограничение с противоположной стороны. Исследования подтверждают то, что многие чувствовали: эти модели проявляют структурный английский уклон, при котором одно и то же намерение, выраженное на неанглийском языке, производит измеримо более слабые ответы [[1]](https://arxiv.org/abs/2504.11833). Уклон уходит глубже поверхностного словарного запаса. Репрезентационный анализ крупных моделей рассуждения показывает, что их внутренние пути рассуждения архитектурно центрированы на английском — не только из-за обучающих данных. Независимо от того, на каком языке поступает запрос, модель сходится к латентному пространству английской формы, прежде чем начать рассуждение [[2]](https://arxiv.org/abs/2601.02996). Разделение языкового представления и субстрата рассуждения выявляет ту же закономерность: движок рассуждения работает лучше всего, когда представленный ему языковой слой — английский [[3]](https://arxiv.org/abs/2505.15257). Следствие не теоретично. В одиннадцати языках и четырёх предметных областях неанглийские запросы демонстрируют последовательное ухудшение как производительности, так и надёжности [[4]](https://arxiv.org/abs/2505.15935).

Два разума с противоречащими целями. Один мыслит яснее всего на родном языке. Другой рассуждает лучше всего на английском.

Prompapa стоит между ними. Не более того.

> **Примечание об эффективности:** Неанглийские языки подвергаются серьезному штрафу по токенам. Например, русский язык часто потребляет значительно больше токенов, чем тот же самый смысл, выраженный на английском. Перевод перед отправкой значительно уменьшает раздувание окна контекста и снижает затраты на API.

### Ссылки

1. Gao et al. (2025). *Could Thinking Multilingually Empower LLM Reasoning?* [arXiv:2504.11833](https://arxiv.org/abs/2504.11833)
2. Liu et al. (2026). *Large Reasoning Models Are (Not Yet) Multilingual Latent Reasoners.* [arXiv:2601.02996](https://arxiv.org/abs/2601.02996)
3. Zhao et al. (2025). *When Less Language is More: Language-Reasoning Disentanglement Makes LLMs Better Multilingual Reasoners.* NeurIPS 2025. [arXiv:2505.15257](https://arxiv.org/abs/2505.15257)
4. Hofman et al. (2025). *MAPS: A Multilingual Benchmark for Agent Performance and Security.* EACL 2026. [arXiv:2505.15935](https://arxiv.org/abs/2505.15935)

## Установка

Требуется [uv](https://docs.astral.sh/uv/). Если не установлен:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Затем установите prompapa:

```bash
uv tool install git+https://github.com/seilk/prompapa
```

## Настройка

Запустите мастер настройки для конфигурации API-ключа:

```bash
papa onboard
```

Это настроит `~/.config/prompapa/config.toml` с вашим ключом Google Cloud Translation API.

### Получение ключа Google Cloud Translation API

> **Бесплатный уровень:** Google Cloud Translation API (Basic) предоставляет **500 000 символов бесплатно каждый месяц**. Сверх этого — $20 за миллион символов. Типичный AI-промпт занимает 100–300 символов, то есть в рамках бесплатного лимита доступно около 1 500–5 000 переводов в день.

1. Перейдите на [console.cloud.google.com](https://console.cloud.google.com) и войдите в аккаунт.
2. Создайте новый проект или выберите существующий.
3. Перейдите в **APIs & Services → Библиотека**, найдите **Cloud Translation API** и нажмите **Включить**.
4. Система предложит активировать платёжный аккаунт. Потребуется карта, но **в рамках бесплатного лимита оплата не взимается**. ([Подробнее о ценах](https://cloud.google.com/translate/pricing))
5. Перейдите в **APIs & Services → Учётные данные → Создать учётные данные → Ключ API**.
6. Скопируйте сгенерированный ключ и вставьте его при запросе `papa onboard`.

## Использование

> ⚠️ **Пользователи OpenCode:** При использовании `papa opencode` сначала отключите вид боковой панели. Prompapa не может правильно изолировать область ввода, когда боковая панель открыта, что вызывает ошибки перевода.

```bash
papa claude # for Claude-Code
papa codex # for Codex
papa opencode # for Opencode
```

> **Примечание:** Инструмент открывается точно так же, как обычно. Два новых горячих клавиши:

| Горячая клавиша | Действие |
|--------|--------|
| `Ctrl+]` | Перевести текущий ввод на английский |
| `Ctrl+Q` | Отменить перевод, восстановить исходный текст |

### Однократный перевод (One-shot)

Переводите текст напрямую из командной строки, не запуская TUI:

```bash
papa -t "버그를 고쳐줘"          # Корейский  → Fix the bug.
papa -t "バグを修正して"          # Японский → Fix the bug.
papa -t "修复这个错误"            # Китайский  → Fix this error.
papa -t "Corrige el error"       # Испанский  → Fix the error.
papa -t "Corrige le bug"         # Французский   → Fix the bug.
papa -t "Behebe den Fehler"      # Немецкий   → Fix the bug.
```

Переведенный результат выводится в stdout, что позволяет легко перенаправлять его в другие инструменты:

```bash
papa -t "이 내용을 클립보드에 복사해줘" | pbcopy
```

## Конфигурация

`~/.config/prompapa/config.toml`:

```toml
provider = "google"
api_key = "your-gcp-translation-api-key"
target_cmd = ["claude"]
preserve_backticks = true
```

`api_key_env` также поддерживается, если вы предпочитаете хранить ключ в переменной окружения:

```toml
provider = "google"
api_key_env = "GOOGLE_API_KEY"
target_cmd = ["claude"]
```

### preserve_backticks

Сохраняет токены, обёрнутые в обратные кавычки, непереведёнными:

```toml
preserve_backticks = true
```

`` `src/auth.ts` `` остаётся точно таким же после перевода.

## Как это работает

Prompapa разветвляет целевой CLI в **PTY (псевдотерминал)**, прозрачно располагаясь между вашей клавиатурой и процессом. Каждое нажатие клавиши проходит без изменений, пока вы не нажмёте `Ctrl+]`.

В этот момент:

1. Считывает текущий ввод с экрана терминала через трекер экрана `pyte`
2. Запускает асинхронный вызов к Google Cloud Translation API
3. Стирает исходный текст точно посчитанными нажатиями backspace (без перерисовки экрана)
4. Вставляет английский результат через bracket paste

Дочерний процесс никогда не останавливается. Интерфейс никогда не перерисовывается. Текст просто... меняется.

## Разработка

```bash
git clone https://github.com/seilk/prompapa
cd prompapa
uv sync
uv run pytest -v
```

Запуск локально без установки:

```bash
uv run papa claude
uv run papa -t "테스트 문장"
```

## Обновление

```bash
papa update
```

Загружает и переустанавливает последнюю версию с GitHub.

## Удаление

```bash
papa uninstall
```

Конфигурация в `~/.config/prompapa/` сохраняется. При необходимости удалите её вручную.

## TODO
- [x] Поддержка `codex` и `opencode`
- [ ] Поддержка боковой панели OpenCode — в настоящее время выдает ошибку, когда боковая панель включена
- [ ] Поддержка перевода через LLM API (OpenAI, Gemini, Claude, ...)
- [ ] Настраиваемый целевой язык перевода, не только английский
