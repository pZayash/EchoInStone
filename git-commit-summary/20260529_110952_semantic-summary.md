# Semantic summary: 20260529_110952

## Контекст

Перенос и адаптация навыка `handoff` из проекта КПСР UNF 2020 в EchoInStone.
Заменена прежняя облегчённая версия навыка (писала в `docs/handoff/`) на богатую
КПСР-версию со структурой «снимок сессии + ссылки на устойчивые артефакты».

Изменений продуктового кода (`EchoInStone/`, `tests/`, `features/`) нет.

## Изменения

- **.cursor/skills/handoff/SKILL.md**: переписан под стек EchoInStone
  (Python 3.12 / Poetry / pytest-bdd, OpenSpec, `memory/`).
  - Проверки: `poetry run pytest` + прогон `echoinstone` вместо BSL/XML.
  - Память: `rg`/SemanticSearch по `memory/`, `memory.md`, `TAGS.md` вместо `qmd`.
  - Навыки: openspec-apply-change, openspec-propose, explore,
    youtube-video-summary, close-chat, sandbox-oneliner.
  - Убраны MCP `dev_dt` и 1C-поиск (нерелевантны).
  - Документы пишутся в `handoffs/` (gitignored), не в `docs/handoff/`.
- **.gitignore**: добавлен каталог `handoffs/` — локальные снимки сессий.

## Технические детали

- `.claude/skills/handoff` — junction на `.cursor/skills/handoff` (обновился автоматически).
- Frontmatter навыка: `argument-hint` (из КПСР) + `project`/`license`/`allowed-tools` (стиль EIS).

## Поведение / UX

Навык `/handoff` теперь пишет снимок сессии в gitignored `handoffs/` и ссылается
на OpenSpec/memory/коммиты, не дублируя их.
