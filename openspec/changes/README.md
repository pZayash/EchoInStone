# Изменения проекта

Здесь хранятся предложения изменений и их реализации.

## Структура

- Каждое изменение имеет свою папку с ID
- В папке находятся файлы:
  - `proposal.md` — описание изменения
  - `design.md` — технические решения
  - `tasks.md` — задачи реализации
  - `specs/` — изменения в спецификациях
  - `.openspec.yaml` — метаданные change

Архив завершённых изменений: `openspec/changes/archive/`.

## Workflow для агентов (навыки)

Точка входа — `.cursor/skills/` (дублируется в `.claude/skills/` для Claude Code):

1. **explore** — исследование, лексика, CONTEXT/ADR (без правок `EchoInStone/**`, `tests/**`, `features/**`)
2. **openspec-propose** — change + артефакты
3. **openspec-apply-change** — реализация по `tasks.md`
4. **openspec-archive-change** — sync delta-spec, перенос в `archive/`

Команды: `/explore` (или `/opsx-explore` — алиас), `/opsx-propose`, `/opsx-apply`, `/opsx-archive`, `/close-chat` (финал сессии).

**Закрытие сессии:** навык **close-chat** — открытые вопросы, archive готовых changes, очистка мусора, коммит только touched-файлов через `/git-summarize-and-commit`.

Контекст проекта: [openspec/project.md](../project.md).
