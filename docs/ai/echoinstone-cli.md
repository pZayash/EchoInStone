# EchoInStone CLI для агентов и терминала

Проект **EchoInStone** — транскрипция, диаризация, выравнивание сегментов и (опционально) анализ видео. Для любой работы с роликами, подкастами и локальными аудио/видео **не пишите однострочники** (`python -c`, heredoc, `sandbox-run` + yt-dlp) — используйте пайплайн репозитория.

## Глобальный шорткат `echoinstone`

В `PATH` (каталог `C:\!Pavl0\.path`, вне репозитория) лежат обёртки:

| Команда | Назначение |
|---------|------------|
| `echoinstone` | Основной CLI: `poetry run python main.py` в корне репозитория |
| `echoinstone-bench` | `benchmark_transcribers.py` |
| `echoinstone-test` | `pytest tests/ features/` |

Доступны в **bash**, **cmd** и **PowerShell** (имена файлов: `echoinstone`, `echoinstone.cmd`, `echoinstone.ps1` и т.д.).

Первый позиционный аргумент и значение `--output_dir` разрешаются **относительно текущей директории** вызова (URL и абсолютные пути не трогаются).

Эквивалент без шортката (из любого каталога):

```bash
poetry --directory "C:/!Pavl0/GitHub/pzayash/EchoInStone" run python main.py <аргументы>
```

В документации и скиллах под **`echoinstone`** имеется в виду эта обёртка; путь к репозиторию в обёртках зашит в `echoinstone*.ps1` / `echoinstone` (bash).

## Запуск

```bash
echoinstone "<audio_input_url_or_path>"
```

`<audio_input_url_or_path>` — YouTube, RSS подкаста, прямой URL аудио/видео или локальный файл.

По умолчанию для YouTube включён **subtitle-first** (субтитры через встроенный `YouTubeDownloader`, затем при необходимости Whisper + pyannote). Полное описание поведения — в [README.md](../../README.md) и `EchoInStone/config.py` (`SUBTITLE_FIRST_*`).

Результаты: каталог `results/{yyMMdd_HHmm}_{название}/` с `speaker_transcriptions.json` и `.csv` (и при анализе видео — `scene_analysis.json`).

## Параметры `main.py`

| Параметр | Описание |
|----------|----------|
| `echo_input` | URL или путь к медиа (обязательный позиционный) |
| `--output_dir` | Куда писать результаты (по умолчанию `results`) |
| `--transcription_output` | Имя JSON с транскриптом (по умолчанию `speaker_transcriptions.json`) |
| `--enable_video_analysis` | Включить сцену/OCR для видео |
| `--disable_video_analysis` | Отключить анализ видео |
| `--scene_output` | Имя JSON сцен (по умолчанию `scene_analysis.json`) |
| `--disable_subtitle_first` | Всегда Whisper + диаризация, без попытки субтитров YouTube |
| `--transcriber_backend` | `auto`, `transformers` или `faster-whisper` |

Примеры:

```bash
# YouTube: сначала субтитры, иначе ASR + диаризация (по умолчанию)
echoinstone "https://www.youtube.com/watch?v=VIDEO_ID"

# Только Whisper + pyannote (долго, со спикерами в JSON)
echoinstone "https://www.youtube.com/watch?v=VIDEO_ID" --disable_subtitle_first

# Локальный файл, свой каталог результатов
echoinstone "./meeting.mp4" --output_dir "./out/meeting"

# Видео со сценами и OCR
echoinstone "https://example.com/demo.mp4" --enable_video_analysis
```

Тесты и бенчмарк:

```bash
echoinstone-test
echoinstone-test tests/test_subtitle_extraction.py -v
echoinstone-bench --help
```

## Агенты: что не делать

- **Не** использовать `sandbox-run`, `python3 -c`, `poetry run python -c` и отдельные yt-dlp-скрипты для извлечения транскрипта YouTube — это дублирует и обходит пайплайн EchoInStone.
- **Не** подменять `echoinstone` однострочниками из навыка sandbox-oneliner; sandbox — только для посторонних сниппетов, не связанных с медиа этого репозитория.
- Скилл [youtube-video-summary](../../.cursor/skills/youtube-video-summary/SKILL.md): `echoinstone`, затем чтение `results/…/speaker_transcriptions.csv` (или `.json`) для резюме — **без** экспортных скриптов.
- Нужен `HUGGING_FACE_TOKEN` в `EchoInStone/config.py` (pyannote), `ffmpeg` в PATH; для OCR — Tesseract (см. README).

## Транскрипт для резюме (агенты)

После `echoinstone` артефакты лежат в каталоге из лога `Output directory:`:

- `speaker_transcriptions.csv` — предпочтительный вход для резюме
- `speaker_transcriptions.json` — запасной вариант

Найти свежий CSV:

```bash
ls -td results/*/speaker_transcriptions.csv 2>/dev/null | head -1
```

Скрипт `export_diarized_txt.py` в навыке — только для **ручного** копирования в `diarization/transcripts/`; агентам не вызывать.
