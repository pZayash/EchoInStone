# Semantic summary: 20260528_120000

## Контекст

Сессия: транскрипт/резюме YouTube через sandbox; скилл `youtube-video-summary`
с fallback на EchoInStone (Whisper + диаризация). Уточнение `/close-chat`:
автокоммит при отсутствии неясностей.

Продуктового кода (`EchoInStone/`, `tests/`, `features/`) нет.

## Изменения

- **youtube-video-summary**: скилл, `/youtube-summary`, скрипты
  `extract_transcript.py` (sandbox VTT), `export_diarized_txt.py`.
- **close-chat**: полный скилл — гейт неясностей → автокоммит touched;
  openspec без Poetry; archive/очистка по необходимости.
- **AGENTS.md**, **close-chat** command: автокоммит через `/close-chat`.

## Не в коммите

- `diarization/transcripts/` — локальный артефакт сессии.

## Поведение

- `/close-chat` коммитит сам, если гейт пройден; иначе только отчёт.
- Вне close-chat коммиты по-прежнему только с явного разрешения.
