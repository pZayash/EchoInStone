# Instructions for AI agents

## Tool usage

Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.
Always use Poetry to run Python commands in this project (e.g., `poetry run python`, `poetry run pytest`).

### Однострочники и быстрые сниппеты → sandbox

Для **разовых** `python3`/`node`/`bash` однострочников (не код проекта EchoInStone) — навык **sandbox-oneliner** (`.cursor/skills/sandbox-oneliner`, симлинк на `~/.claude/skills/sandbox-oneliner`). Запуск через **`sandbox-run`** из `C:\!Pavl0\.path` — контейнер `agent-sandbox`, без bind mount проекта.

```text
sandbox-run -Command 'python3 -c "print(1+1)"'
sandbox-run -Files data.csv -Command 'python3 -c "print(open(\"data.csv\").read()[:80])"'
```

Не вызывать `poetry run python -c ...` и не создавать временные `.py` на хосте для таких задач: `sandbox-run` можно один раз allowlist'ить в Cursor вместо подтверждения каждого однострочника. Код EchoInStone, тесты и pipeline — по-прежнему через Poetry на хосте.

## OpenSpec workflow

Перед proposal: навык **explore** (`.cursor/skills/explore/`, команда `/explore`) — исследование без правок `EchoInStone/**`. Далее `openspec-propose` → `openspec-apply-change` → `openspec-archive-change`. См. [openspec/changes/README.md](openspec/changes/README.md).

В конце сессии: **close-chat** (`/close-chat`) — автокоммит touched, если нет неясностей (иначе отчёт); перед этим archive/очистка. Вне `/close-chat` коммиты — только с явного разрешения пользователя.
