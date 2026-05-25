# OpenSpec archive: всегда sync + archive

## Контекст

Workflow `openspec-archive-change` и шаг 1 `close-chat`.

## Факт

Без sync основной `openspec/specs/` расходится с фактически внедрённой capability.

## Решение / правило

- При архивации OpenSpec change по умолчанию делать sync delta-spec в `openspec/specs/<capability>/spec.md`, затем перенос в `openspec/changes/archive/YYYY-MM-DD-<name>/`.
- Не задавать повторно вопрос про sync, если пользователь явно не сказал «без sync» в текущем диалоге.

## Теги

openspec, archive, sync, workflow, specs

## Дата и источник

2026-05-25, адаптация из КПСР UNF 2020 (`memory/2026-05-18-openspec-always-sync-and-archive.md`).
