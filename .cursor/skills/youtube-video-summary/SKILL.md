---
name: youtube-video-summary
description: >-
  Транскрипт и резюме YouTube через EchoInStone (echoinstone): subtitle-first
  или Whisper + диаризация. Источник — speaker_transcriptions.csv/json в results/.
  Триггеры: ссылка на YouTube, «ролик», «видео», «резюме ролика», вопросы по содержанию.
argument-hint: "YOUTUBE_URL"
---

# YouTube → транскрипт → резюме

Пользователь даёт **ссылку на YouTube** (или id). Нужны: надёжный текст ролика и **резюме** для обсуждения и follow-up вопросов.

## Зависимости

- **EchoInStone CLI** — глобальный шорткат **`echoinstone`** (bash / cmd / PowerShell) или `poetry run python main.py` из корня репозитория. Параметры и примеры: [docs/ai/echoinstone-cli.md](../../../docs/ai/echoinstone-cli.md), [README.md](../../../README.md).
- **Не использовать** `sandbox-run`, `python -c`, heredoc, `poetry run python` для экспорта/парсинга транскрипта и **не** вызывать `export_diarized_txt.py` — только пайплайн `echoinstone` + чтение артефактов в `results/` (см. [AGENTS.md](../../../AGENTS.md)).

## Чек-лист

```
- [ ] 1. Распарсить URL → 11-символьный video id
- [ ] 2. echoinstone "URL" (subtitle-first по умолчанию)
- [ ] 3. При необходимости полной диаризации: --disable_subtitle_first
- [ ] 4. Найти каталог results/… с speaker_transcriptions.csv (или .json)
- [ ] 5. Прочитать CSV/JSON как есть → резюме (язык сообщения пользователя)
- [ ] 6. Опционально: summary.md в том же каталоге (шаблон summarizev2)
- [ ] 7. При follow-up — читать тот же CSV/JSON, не гонять echoinstone заново
```

## 1. Запуск EchoInStone

Из **любого каталога** (пути в аргументах разрешаются обёрткой):

```bash
echoinstone "https://www.youtube.com/watch?v=VIDEO_ID"
```

- По умолчанию **subtitle-first** для YouTube (быстро, если есть субтитры).
- Выход: `results/{yyMMdd_HHmm}_{название}/speaker_transcriptions.json` и **`speaker_transcriptions.csv`**.
- В логе строка `Output directory: results\…` — это канонический путь сессии.
- Предупредить о времени и железе, если понадобится `--disable_subtitle_first` (Whisper + pyannote, `HUGGING_FACE_TOKEN`, `ffmpeg`).

### Когда добавить флаги

| Задача | Команда |
|--------|---------|
| Обычный ролик / резюме | `echoinstone "URL"` |
| Нужны спикеры, субтитров нет или subtitle-first не подошёл | `echoinstone "URL" --disable_subtitle_first` |
| Свой каталог результатов | `echoinstone "URL" --output_dir results/run-VIDEO_ID` |
| Анализ сцен/OCR | `echoinstone "URL" --enable_video_analysis` |

Полная таблица аргументов — [docs/ai/echoinstone-cli.md](../../../docs/ai/echoinstone-cli.md).

## 2. Источник текста (без экспортных скриптов)

**Агент читает артефакты пайплайна напрямую.** Не запускать `poetry run python …/export_diarized_txt.py` и любые другие скрипты из `.cursor/skills/youtube-video-summary/scripts/` для резюме.

### Найти каталог результата

1. Взять путь из вывода `echoinstone` (`Output directory: …`), **или**
2. Свежий каталог:
   ```bash
   ls -td results/*/speaker_transcriptions.csv 2>/dev/null | head -1
   ```
3. Сверить video id: в CSV/JSON первая строка с `start=0`, `end=0` часто содержит URL ролика в колонке `text`.

Канонические файлы (в одном каталоге):

| Файл | Когда использовать |
|------|-------------------|
| `speaker_transcriptions.csv` | **Предпочтительно** — удобно читать агенту |
| `speaker_transcriptions.json` | Если CSV нет или не парсится |

### Формат CSV (как отдаёт EchoInStone)

Колонки: `speaker`, `start`, `end`, `text` (секунды с плавающей точкой).

- Строка метаданных: пустой `speaker`, `start=0`, `end=0`, в `text` — URL.
- Остальные строки — фрагменты речи по времени; `speaker` может быть пустым (subtitle-first) или `SPEAKER_XX` (диаризация).

Читать файл **как есть** (без препроцессинга, без `python -c`). Для развёрнутого markdown-отчёта с таймкодами — команда [/summarizev2](../../commands/summarizev2.md): вход = тот же CSV, выход = `summary.md` **в каталоге results/…** (не перезаписывать существующий — `summary_1.md` и т.д.).

### Источник в резюме

Указать, что реально использовал пайплайн: **subtitle-first** или **Whisper + pyannote** (по логу `echoinstone` / `app.log`).

## 3. Резюме (обязательный результат)

Язык резюме = **язык сообщения пользователя** (текст ролика — на языке субтитров/ASR, термины не переводить).

```markdown
## {Title}

**Канал:** … · **Длительность:** … · **Источник:** EchoInStone (subtitle-first / Whisper + диаризация)

### О чём
3–6 конкретных буллетов.

### Ключевые тезисы
Главные выводы, с которыми можно спорить или уточнять.

### Ограничения
- Возможные ошибки распознавания / субтитров.
- Спонсорские вставки — кратко, если есть.

**Транскрипт:** `results/…/speaker_transcriptions.csv` — можно задавать вопросы по содержанию.
```

## 4. Вопросы позже

Читать тот же `speaker_transcriptions.csv` (или `.json`) в `results/…`. Повторный `echoinstone` — только по запросу «обнови транскрипт».

Если за ту же сессию уже есть `summary.md` в каталоге results — можно опираться на него для уточнений, но для нового полного резюме снова читать исходный CSV/JSON.

## Не делать

- Не вызывать `sandbox-run`, `extract_transcript.py`, yt-dlp-однострочники для YouTube-транскрипта.
- Не использовать `python3 -c`, heredoc-Python, `poetry run python -c` для извлечения/форматирования текста ролика.
- **Не** запускать `export_diarized_txt.py` / `format_saved_transcript.py` в агентском workflow.
- Не коммитить `results/` (и старые `diarization/transcripts/`, если есть) без просьбы пользователя.
- Не запускать `--disable_subtitle_first`, если subtitle-first уже дал пригодный `speaker_transcriptions.csv`.

## Скрипты в репозитории (только для людей / legacy)

| Файл | Для агентов |
|------|-------------|
| [scripts/export_diarized_txt.py](scripts/export_diarized_txt.py) | **Не использовать** — дублирует CSV; оставлен для ручного экспорта в `diarization/transcripts/` |
| [scripts/extract_transcript.py](scripts/extract_transcript.py) | **Не использовать** — устаревший VTT/sandbox-путь |
| [scripts/format_saved_transcript.py](scripts/format_saved_transcript.py) | **Не использовать** |
