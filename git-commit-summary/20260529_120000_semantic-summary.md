# Semantic summary: 20260529_120000

## Контекст

Сессия: резюме YouTube-ролика (PuMpRwzHVj8) через `echoinstone` + переработка workflow
навыка `youtube-video-summary` по запросу пользователя — убрать обязательный вызов
`export_diarized_txt.py` (Poetry зависал/прерывался).

## Изменения

- **youtube-video-summary**: агент читает `results/…/speaker_transcriptions.csv` (или `.json`);
  экспортные скрипты помечены legacy/manual only.
- **youtube-summary** (команда), **AGENTS.md**, **docs/ai/echoinstone-cli.md**: согласованы с новым потоком.
- **export_diarized_txt.py**: docstring — не вызывать из agent workflow.

## Не вошло в коммит

- `results/**` — артефакт транскрипта/резюме ролика (локально, в `.gitignore`).
- `memory.md` — untracked шаблон; не создавался в этой сессии как часть правки навыка.
- Продуктовый код `EchoInStone/**` не менялся.

## OpenSpec

Активных changes нет (`openspec list` → `[]`). Archive не выполнялся.
