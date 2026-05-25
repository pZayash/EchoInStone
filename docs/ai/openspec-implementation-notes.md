# Журнал реализации OpenSpec (`implementation-notes.md`)

> © Thariq (@trq212). Идея:
> [пост в X](https://x.com/trq212/status/2056415973125796184) —
> running implementation notes при исполнении spec.

## Назначение

Опциональный Markdown-файл в папке активного change. Агент создаёт и дописывает
его во время
[openspec-apply-change](../../.cursor/skills/openspec-apply-change/SKILL.md),
если при реализации появляется информация, которой нет в `specs/**`,
`design.md`, `tasks.md`.

Файл **не** архивируется вместе с change: перед
[openspec-archive-change](../../.cursor/skills/openspec-archive-change/SKILL.md)
пользователь просматривает журнал, переносит ценное при необходимости
и **удаляет** файл.

## Путь и формат

- Путь: `openspec/changes/<change-name>/implementation-notes.md`
- Только Markdown (не HTML).

## Когда создавать

Создавать **по необходимости**, не на каждый apply. Триггеры:

- решение не описано в spec/design;
- отступление от `tasks.md` или `design.md`;
- tradeoff «A vs B», выбранный на месте;
- риск, долг, ручная приёмка — важно для ревьюера;
- пользователь просит вести журнал.

Если отступлений нет — файл не создавать.

## Когда дописывать

После каждого существенного отступления или решения в сессии apply.
Кратко: дата (опционально), контекст, решение, почему.

## Чего не писать

- дубли `design.md` / `proposal.md` без новой информации;
- построчный лог чата;
- секреты, пароли, токены (в т.ч. `HUGGING_FACE_TOKEN`);
- замена обновления артефактов — если меняется контракт,
  сначала правка spec/design/tasks, журнал фиксирует **факт** отклонения.

## Шаблон

```markdown
# Implementation notes: <change-name>

> © Thariq (@trq212). [Источник идеи](https://x.com/trq212/status/2056415973125796184)

Журнал реализации (опционально). Удалить перед archive change.

## Вне spec

- …

## Отступления от design / tasks

- …

## Tradeoffs

- …

## Для ревьюера

- …
```

Пустые секции удалять.

## Связь с другими артефактами

| Артефакт | Роль |
| --- | --- |
| `design.md` | План до кода |
| `implementation-notes.md` | Факт отклонений при apply |
| `memory/` | Стабильные уроки после разбора notes перед archive |
| `close-chat` | На шаге 0 читает notes; на шаге 1 — удаление перед archive |

## Archive

См. шаг про `implementation-notes.md` в
[openspec-archive-change](../../.cursor/skills/openspec-archive-change/SKILL.md):
файл не переносится в `openspec/changes/archive/` —
только удаление после ревью пользователем.
