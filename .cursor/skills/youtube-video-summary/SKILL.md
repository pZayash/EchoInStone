---
name: youtube-video-summary
description: >-
  Транскрипт и резюме YouTube через EchoInStone (echoinstone): subtitle-first
  или Whisper + диаризация. Сохранение в diarization/transcripts/. Триггеры:
  ссылка на YouTube, «ролик», «видео», «резюме ролика», вопросы по содержанию.
argument-hint: "YOUTUBE_URL"
---

# YouTube → транскрипт → резюме

Пользователь даёт **ссылку на YouTube** (или id). Нужны: надёжный текст ролика и **резюме** для обсуждения и follow-up вопросов.

## Зависимости

- **EchoInStone CLI** — глобальный шорткат **`echoinstone`** (bash / cmd / PowerShell) или `poetry run python main.py` из корня репозитория. Параметры и примеры: [docs/ai/echoinstone-cli.md](../../../docs/ai/echoinstone-cli.md), [README.md](../../../README.md).
- **Не использовать** `sandbox-run`, `python -c`, heredoc и отдельные yt-dlp-однострочники для транскрипта — только пайплайн проекта (см. [AGENTS.md](../../../AGENTS.md)).

## Чек-лист

```
- [ ] 1. Распарсить URL → 11-символьный video id
- [ ] 2. echoinstone "URL" (subtitle-first по умолчанию)
- [ ] 3. При необходимости полной диаризации: --disable_subtitle_first
- [ ] 4. Экспорт → diarization/transcripts/{VIDEO_ID}.diarized.txt
- [ ] 5. Ответ: метаданные + резюме (язык сообщения пользователя) + путь к файлу
- [ ] 6. При follow-up — читать сохранённый файл, не гонять echoinstone заново
```

## 1. Запуск EchoInStone

Из **любого каталога** (пути в аргументах разрешаются обёрткой):

```bash
echoinstone "https://www.youtube.com/watch?v=VIDEO_ID"
```

- По умолчанию **subtitle-first** для YouTube (быстро, если есть субтитры).
- Выход: `results/{yyMMdd_HHmm}_{название}/speaker_transcriptions.json` (+ `.csv`).
- Предупредить о времени и железе, если понадобится `--disable_subtitle_first` (Whisper + pyannote, `HUGGING_FACE_TOKEN`, `ffmpeg`).

Найти свежий результат:

```bash
ls -td results/*/speaker_transcriptions.json 2>/dev/null | head -1
```

### Когда добавить флаги

| Задача | Команда |
|--------|---------|
| Обычный ролик / резюме | `echoinstone "URL"` |
| Нужны спикеры, субтитров нет или subtitle-first не подошёл | `echoinstone "URL" --disable_subtitle_first` |
| Свой каталог результатов | `echoinstone "URL" --output_dir diarization/run-VIDEO_ID` |
| Анализ сцен/OCR | `echoinstone "URL" --enable_video_analysis` |

Полная таблица аргументов — [docs/ai/echoinstone-cli.md](../../../docs/ai/echoinstone-cli.md).

## 2. Экспорт в `diarization/transcripts/`

Из **корня репозитория** (Poetry):

```bash
poetry run python .cursor/skills/youtube-video-summary/scripts/export_diarized_txt.py \
  "results/.../speaker_transcriptions.json" \
  "diarization/transcripts/VIDEO_ID.diarized.txt" \
  --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

Формат файла:

```text
# Source: EchoInStone (Whisper + pyannote diarization)
# URL: https://www.youtube.com/watch?v=VIDEO_ID
# Input: results/.../speaker_transcriptions.json

---TRANSCRIPT---
[SPEAKER_00] …
```

В резюме указать источник: **subtitle-first** или **Whisper + pyannote** (по тому, что реально использовал пайплайн; при сомнении — смотреть логи `app.log` / вывод `echoinstone`).

## 3. Резюме (обязательный результат)

Язык резюме = **язык сообщения пользователя**.

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

**Файл:** `diarization/transcripts/…` — можно задавать вопросы по содержанию.
```

## 4. Вопросы позже

Читать сохранённый транскрипт. Повторный `echoinstone` — только по запросу «обнови транскрипт».

## Не делать

- Не вызывать `sandbox-run`, `extract_transcript.py`, yt-dlp-однострочники для YouTube-транскрипта.
- Не использовать `python3 -c`, heredoc-Python, `poetry run python -c` для извлечения/форматирования текста ролика.
- Не коммитить `diarization/transcripts/` и `results/` без просьбы пользователя.
- Не запускать `--disable_subtitle_first`, если subtitle-first уже дал пригодный `speaker_transcriptions.json`.

## Вспомогательные скрипты

| Файл | Назначение |
|------|------------|
| [scripts/export_diarized_txt.py](scripts/export_diarized_txt.py) | `speaker_transcriptions.json` → `diarization/transcripts/*.txt` |
| [scripts/extract_transcript.py](scripts/extract_transcript.py) | **Устарело для агентов** — только VTT в sandbox; не использовать вместо `echoinstone` |
