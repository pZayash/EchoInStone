# Instructions for AI agents

## Tool usage

Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.
Always use Poetry to run Python commands in this project (e.g., `poetry run python`, `poetry run pytest`).

### Медиа, YouTube, транскрипция → `echoinstone`

Для роликов, подкастов, локального аудио/видео, транскрипта и диаризации **не писать однострочники** и **не** использовать `sandbox-run` / yt-dlp-сниппеты. Запускайте пайплайн проекта:

```text
echoinstone "https://www.youtube.com/watch?v=VIDEO_ID"
```

Глобальный шорткат в PATH (`C:\!Pavl0\.path`: `echoinstone`, `echoinstone.cmd`, `echoinstone.ps1`; также `echoinstone-test`, `echoinstone-bench`). Параметры CLI: [docs/ai/echoinstone-cli.md](docs/ai/echoinstone-cli.md), [README.md](README.md#usage). Резюме по YouTube: навык [youtube-video-summary](.cursor/skills/youtube-video-summary/SKILL.md).

Эквивалент: `poetry --directory <корень EchoInStone> run python main.py …`. Экспорт текста для резюме — `export_diarized_txt.py` (см. скилл).

### Однострочники (не медиа) → sandbox

Для **разовых** `python3`/`node`/`bash` сниппетов **вне** транскрипции/диаризации/YouTube — навык **sandbox-oneliner** (`.cursor/skills/sandbox-oneliner`). Запуск: **`sandbox-run`** из `C:\!Pavl0\.path`, контейнер `agent-sandbox`.

```text
sandbox-run -Command 'python3 -c "print(1+1)"'
```

Не вызывать `poetry run python -c ...`, `python3 -c ...` и heredoc-Python на хосте для таких задач. Код EchoInStone, тесты и `echoinstone-test` — через Poetry / шорткаты, не через sandbox.

## OpenSpec workflow

Перед proposal: навык **explore** (`.cursor/skills/explore/`, команда `/explore`) — исследование без правок `EchoInStone/**`. Далее `openspec-propose` → `openspec-apply-change` → `openspec-archive-change`. См. [openspec/changes/README.md](openspec/changes/README.md).

В конце сессии: **close-chat** (`/close-chat`) — автокоммит touched, если нет неясностей (иначе отчёт); перед этим archive/очистка. Вне `/close-chat` коммиты — только с явного разрешения пользователя.
