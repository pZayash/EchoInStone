# Semantic summary: 260528_164634

## Контекст

Сессия: обзор YouTube `qEMx5CURC_w`, уточнение «песочница» → затем правка
документации: медиа/YouTube через **`echoinstone`**, без sandbox-однострочников
и устаревшего `extract_transcript.py` в основном пути агентов.

Продуктового кода (`EchoInStone/`, `tests/`, `features/`) нет.

## Изменения

- **docs/ai/echoinstone-cli.md**: шорткаты PATH, флаги `main.py`, запрет one-liners для транскрипции.
- **AGENTS.md**: секция «Медиа → echoinstone»; sandbox только для посторонних сниппетов.
- **youtube-video-summary/SKILL.md**, **youtube-summary.md**: пайплайн `echoinstone` → export → резюме.
- **README.md**, **openspec/project.md**, **.cursorrules**: ссылки на CLI.
- **extract_transcript.py**: docstring — deprecated для агентов.

## Не в коммите

- `diarization/transcripts/qEMx5CURC_w.ru.txt` (в `.gitignore`).
- `C:\!Pavl0\.path\echoinstone*` (вне репозитория).

## Поведение

- `/close-chat` автокоммит при пустом OpenSpec и без неясностей.
