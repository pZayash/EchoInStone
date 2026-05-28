# Instructions for AI agents

## Tool usage

Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.
Always use Poetry to run Python commands in this project (e.g., `poetry run python`, `poetry run pytest`).

## OpenSpec workflow

Перед proposal: навык **explore** (`.cursor/skills/explore/`, команда `/explore`) — исследование без правок `EchoInStone/**`. Далее `openspec-propose` → `openspec-apply-change` → `openspec-archive-change`. См. [openspec/changes/README.md](openspec/changes/README.md).

В конце сессии: **close-chat** (`/close-chat`) — автокоммит touched, если нет неясностей (иначе отчёт); перед этим archive/очистка. Вне `/close-chat` коммиты — только с явного разрешения пользователя.
