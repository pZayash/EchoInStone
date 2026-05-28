---
name: youtube-video-summary
description: >-
  Извлекает транскрипт YouTube (авто-субтитры через yt-dlp в docker sandbox;
  при отсутствии субтитров — Whisper + диаризация через EchoInStone main.py),
  сохраняет в diarization/transcripts/ и выдаёт структурированное резюме на языке
  пользователя. Триггеры: ссылка на YouTube, «ролик», «видео», «резюме ролика»,
  «извлеки текст», вопросы по содержанию видео.
argument-hint: "YOUTUBE_URL [--sub-lang en-orig,en|ru,...]"
---

# YouTube → транскрипт → резюме

Пользователь даёт **ссылку на YouTube** (или id). Нужны: надёжный текст ролика и **резюме** для обсуждения и follow-up вопросов.

## Зависимости

- **sandbox-oneliner** (`~/.claude/skills/sandbox-oneliner/`) — однострочники в `agent-sandbox` через `sandbox-run`.
- На хосте YouTube часто отвечает **HTTP 429**; извлечение — **только через sandbox**, если пользователь не настаивает на хосте.

## Чек-лист

```
- [ ] 1. Распарсить URL → 11-символьный video id
- [ ] 2. Быстрый путь: extract_transcript.py в sandbox
- [ ] 3. Если NO_SUBTITLES / нет VTT → EchoInStone (транскрипция + диаризация)
- [ ] 4. Сохранить diarization/transcripts/{VIDEO_ID}.{lang|diarized}.txt
- [ ] 5. Ответ: метаданные + резюме (язык сообщения пользователя) + путь к файлу
- [ ] 6. При follow-up — читать сохранённый файл, не качать заново
```

## 1. Язык субтитров

| Ситуация | `--sub-lang` |
|----------|----------------|
| По умолчанию (EN) | `en-orig,en` |
| Резюме по-русски, ролик на EN | субтитры `en-orig,en`, резюме на русском |
| Нужны русские субтитры | `ru,en-orig,en` |

Ручных субтитров нет → в ответе указать **авто-субтитры**.

## 2. Извлечение (sandbox)

Путь к скрипту **от корня репозитория**:

`.cursor/skills/youtube-video-summary/scripts/extract_transcript.py`

```text
sandbox-run -Files ".cursor/skills/youtube-video-summary/scripts/extract_transcript.py" -Command 'python3 extract_transcript.py "YOUTUBE_URL" --sub-lang en-orig,en' 2>/dev/null
```

Подставить URL и `--sub-lang`. Stderr на хосте — в `/dev/null`, чтобы предупреждения yt-dlp не попали в файл.

При сбое: проверить контейнер (см. sandbox-oneliner), один retry. Не падать на host yt-dlp без явной просьбы.

**Нет субтитров** — скрипт печатает `NO_SUBTITLES|true` и exit code `2` → перейти к §3 (EchoInStone).  
Другая ошибка sandbox (сеть, 429) — один retry; если снова неудача, можно §3 или спросить пользователя.

## 3. Fallback: транскрипция + диаризация (EchoInStone)

Когда у ролика **нет** авто-/ручных субтитров (или sandbox не смог их скачать).

Из **корня репозитория**, через Poetry (см. [README.md](../../../README.md)):

```bash
poetry run python main.py "YOUTUBE_URL" --disable_subtitle_first
```

- `--disable_subtitle_first` — не использовать subtitle-first даже если yt-dlp на хосте что-то найдёт; нужны **Whisper + pyannote** и спикеры.
- Выход: `results/{yyMMdd_HHmm}_{название}/speaker_transcriptions.json` (+ `.csv`).
- Долго, нужны `ffmpeg`, зависимости Poetry, `HUGGING_FACE_TOKEN` в `EchoInStone/config.py` (pyannote).
- Предупредить пользователя о времени и железе (GPU/XPU по README).

Найти свежий результат (пример):

```bash
ls -td results/*/speaker_transcriptions.json 2>/dev/null | head -1
```

Экспорт в `diarization/transcripts/` для резюме и Q&A:

```bash
poetry run python .cursor/skills/youtube-video-summary/scripts/export_diarized_txt.py \
  "results/.../speaker_transcriptions.json" \
  "diarization/transcripts/{VIDEO_ID}.diarized.txt" \
  --url "YOUTUBE_URL"
```

В резюме указать источник: **Whisper + pyannote diarization** (со спикерами `[SPEAKER_XX]`, если есть).

## 4. Сохранение (субтитры)

```text
diarization/transcripts/{VIDEO_ID}.{lang_hint}.txt
```

Создать `diarization/transcripts/` при отсутствии. Формат файла:

```text
# {TITLE}
# Channel: {CHANNEL} | Duration: {DURATION_SEC}s | Words: {WORDS}
# URL: https://www.youtube.com/watch?v={VIDEO_ID}
# Source: YouTube auto-captions ({SUB_LANG})

---TRANSCRIPT---
(тело после маркера из stdout)
```

## 5. Резюме (обязательный результат)

Язык резюме = **язык сообщения пользователя**.

```markdown
## {Title}

**Канал:** … · **Длительность:** … · **Источник:** авто-субтитры *или* Whisper + диаризация …

### О чём
3–6 конкретных буллетов.

### Ключевые тезисы
Главные выводы, с которыми можно спорить или уточнять.

### Ограничения
- Возможные ошибки распознавания.
- Спонсорские вставки / призывы — кратко, если есть.

**Файл:** `diarization/transcripts/…` — можно задавать вопросы по содержанию.
```

## 6. Вопросы позже

Читать сохранённый транскрипт. Повторное скачивание — только по запросу «обнови транскрипт».

## Не делать

- Не монтировать проект в docker ради yt-dlp.
- Не коммитить `diarization/transcripts/` и `results/` без просьбы пользователя.
- Не запускать EchoInStone pipeline, если sandbox уже дал нормальный транскрипт (избыточно).

## Скрипты

| Файл | Назначение |
|------|------------|
| [scripts/extract_transcript.py](scripts/extract_transcript.py) | VTT в sandbox; `NO_SUBTITLES\|true` + exit 2 |
| [scripts/export_diarized_txt.py](scripts/export_diarized_txt.py) | `speaker_transcriptions.json` → `diarization/transcripts/*.txt` |
