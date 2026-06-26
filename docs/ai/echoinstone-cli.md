# EchoInStone CLI для агентов и терминала

Проект **EchoInStone** — транскрипция, диаризация, выравнивание сегментов и (опционально) визуальное обогащение видео. Для любой работы с роликами, подкастами и локальными аудио/видео **не пишите однострочники** (`python -c`, heredoc, `sandbox-run` + yt-dlp) — используйте пайплайн репозитория.

## Глобальный шорткат `echoinstone`

В `PATH` (каталог `C:\!Pavl0\.path`, вне репозитория) лежат обёртки:

| Команда | Назначение |
|---------|------------|
| `echoinstone` | Основной CLI: `poetry run python main.py` в корне репозитория |
| `echoinstone-bench` | `benchmark_transcribers.py` |
| `echoinstone-test` | `pytest tests/ features/` |

## Запуск

```bash
echoinstone "<audio_input_url_or_path>"
```

Результаты: каталог `results/{yyMMdd_HHmm}_{название}/` с `speaker_transcriptions.json` и `.csv`.

При `--enable_video_analysis` дополнительно: `job_metadata.json`, `visual_enrichment.json`, `keyframes/`, `scene_analysis.json`.

## Параметры `main.py`

| Параметр | Описание |
|----------|----------|
| `echo_input` | URL или путь к медиа (необязателен в pass 2) |
| `--output_dir` | Куда писать результаты (по умолчанию `results`) |
| `--transcription_output` | Имя JSON с транскриптом |
| `--enable_video_analysis` | Keyframe + scene-text OCR |
| `--disable_video_analysis` | Отключить визуальный анализ |
| `--scene_output` | Имя JSON сцен |
| `--job-dir` | Pass 2: каталог job из pass 1 |
| `--extract-at` | Pass 2: метки времени (`5:00,40:00`) |
| `--disable_subtitle_first` | Всегда Whisper + диаризация |
| `--transcriber_backend` | `auto`, `transformers`, `faster-whisper` |

## Two-pass enrichment (агенты)

**Pass 1** — транскрипция + опционально полный визуальный анализ:

```bash
poetry install --extras scene-ocr
echoinstone "./webinar.mp4" --enable_video_analysis
```

**Pass 2** — точечное извлечение keyframe + OCR по меткам из суммаризации:

```bash
echoinstone --job-dir "results/260626_0917_webinar" --extract-at "5:00,40:00"
```

Артефакты для обогащения резюме:

- `visual_enrichment.json` — OCR-текст по времени
- `keyframes/manifest.json` + `keyframes/*.png` — картинки
- `job_metadata.json` — `source_video_path` для pass 2

## Транскрипт для резюме (агенты)

После pass 1:

- `speaker_transcriptions.csv` — основной вход для резюме
- `visual_enrichment.json` — опционально для on-screen контента

```bash
ls -td results/*/speaker_transcriptions.csv 2>/dev/null | head -1
```

## Зависимости

- `HUGGING_FACE_TOKEN` в `EchoInStone/config.py` (pyannote)
- `ffmpeg` в PATH
- Scene-text OCR: `poetry install --extras scene-ocr` (EasyOCR `ru`+`en`)

Скилл [youtube-video-summary](../../.cursor/skills/youtube-video-summary/SKILL.md): `echoinstone` → CSV/JSON; при видео — также `visual_enrichment.json`.
