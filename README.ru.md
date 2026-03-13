<p align="center">
  <img src="assets/prompapa-banner.png" alt="prompapa" width="800" />
</p>

<p align="center">
  <em>Пишите на родном языке. Нажмите <code>Ctrl+T</code> в <strong>Claude Code</strong>. Смотрите, как это становится безупречным английским.</em>
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

<p align="center"><em><strong>Пишите на <em>любом языке</em> — нажмите <code>Ctrl+T</code> для перевода на английский. Нажмите <code>Ctrl+Y</code> для отмены.</strong></em></p>

## Зачем это нужно

Язык — не нейтральный сосуд для мысли. Слова, к которым мы обращаемся первыми, структура, которую мы навязываем, ещё не понимая, что имеем в виду, инстинкт, предшествующий артикуляции — всё это родное. Принуждение этого процесса через второй язык не просто замедляет его. Оно тихо переформирует его.

ИИ-ассистенты для программирования несут аналогичное ограничение с противоположной стороны. Исследования подтверждают то, что многие чувствовали: эти модели проявляют структурный английский уклон, при котором одно и то же намерение, выраженное на неанглийском языке, производит измеримо более слабые ответы [[1]](https://arxiv.org/abs/2504.11833). Уклон уходит глубже поверхностного словарного запаса. Репрезентационный анализ крупных моделей рассуждения показывает, что их внутренние пути рассуждения архитектурно центрированы на английском — не только из-за обучающих данных. Независимо от того, на каком языке поступает запрос, модель сходится к латентному пространству английской формы, прежде чем начать рассуждение [[2]](https://arxiv.org/abs/2601.02996). Разделение языкового представления и субстрата рассуждения выявляет ту же закономерность: движок рассуждения работает лучше всего, когда представленный ему языковой слой — английский [[3]](https://arxiv.org/abs/2505.15257). Следствие не теоретично. В одиннадцати языках и четырёх предметных областях неанглийские запросы демонстрируют последовательное ухудшение как производительности, так и надёжности [[4]](https://arxiv.org/abs/2505.15935).

Два разума с противоречащими целями. Один мыслит яснее всего на родном языке. Другой рассуждает лучше всего на английском.

Prompapa стоит между ними. Не более того.

### Ссылки

1. Gao et al. (2025). *Could Thinking Multilingually Empower LLM Reasoning?* arXiv:2504.11833
2. Liu et al. (2026). *Large Reasoning Models Are (Not Yet) Multilingual Latent Reasoners.* arXiv:2601.02996
3. Zhao et al. (2025). *When Less Language is More: Language-Reasoning Disentanglement Makes LLMs Better Multilingual Reasoners.* NeurIPS 2025. arXiv:2505.15257
4. Hofman et al. (2025). *MAPS: A Multilingual Benchmark for Agent Performance and Security.* EACL 2026. arXiv:2505.15935

## Установка

Требуется [uv](https://docs.astral.sh/uv/). Установите один раз, затем:

```bash
uv tool install git+https://github.com/seilk/prompapa
```

## Настройка

Запустите мастер настройки для конфигурации API-ключа:

```bash
papa onboard
```

Это настроит `~/.config/prompapa/config.toml` с вашим ключом Google Cloud Translation API.

Ещё нет ключа? Мастер проведёт вас через его получение.

## Использование

```bash
papa claude
```

Инструмент открывается точно так же, как обычно. Два новых горячих клавиши:

| Горячая клавиша | Действие |
|--------|--------|
| `Ctrl+T` | Перевести текущий ввод на английский |
| `Ctrl+Y` | Отменить — восстановить исходный текст |

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

Prompapa разветвляет целевой CLI в **PTY (псевдотерминал)**, прозрачно располагаясь между вашей клавиатурой и процессом. Каждое нажатие клавиши проходит без изменений — пока вы не нажмёте `Ctrl+T`.

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
```

## Удаление

```bash
papa uninstall
```

Конфигурация в `~/.config/prompapa/` сохраняется. При необходимости удалите её вручную.

## TODO
- [ ] Поддержка `opencode`
- [ ] Поддержка перевода через LLM API (OpenAI, Gemini, Claude, ...)
