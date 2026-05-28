# Semantic summary: 20260528_150500

## Контекст

Сессия: `/youtube-video-summary` и уточнение «однострочники только через
песочницу». Закрытие `/close-chat` — только документация и скрипты навыка;
транскрипты и резюме роликов в репозиторий не входят.

Продуктового кода (`EchoInStone/`, `tests/`, `features/`) нет.

## Изменения

- **youtube-video-summary**: SKILL §2 — один `sandbox-run`, `--save-format`,
  запрет host `python -c`; скрипт `format_saved_transcript.py` (pipe-вариант).
- **extract_transcript.py**: флаг `--save-format` для редиректа в
  `diarization/transcripts/*.txt`.
- **AGENTS.md**, **youtube-summary** command: sandbox-only, запись через `> file`.

## Не в коммите

- `diarization/transcripts/**` (локальные транскрипты; удалены по запросу).
- `git-commit-summary/20260528_1423_*`, `143738_*` — уже в истории ветки;
  этот batch не трогает их содержимое.
- `.cursor/skills/sandbox-oneliner` — симлинк вне git (см. `.gitignore`).

## Поведение

- Извлечение YouTube: `sandbox-run` + `extract_transcript.py --save-format 2>/dev/null` → redirect.
