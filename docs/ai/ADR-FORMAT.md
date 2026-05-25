# Формат ADR

ADR фиксирует архитектурное решение и причину выбора.

## Где хранить

- Каталог: `docs/adr/`.
- Создавать каталог лениво: только при первом ADR.
- Имена файлов по порядку: `0001-slug.md`, `0002-slug.md`.

## Минимальный шаблон

```md
# {Short title of the decision}

{1-3 sentences: what's the context, what did we decide, and why.}
```

Этого достаточно: ADR может быть одним абзацем.

## Опциональные секции

Добавлять только если есть реальная ценность:

- `Status` (`proposed`, `accepted`, `deprecated`, `superseded by ADR-NNNN`)
- `Considered options`
- `Consequences`

## Когда предлагать ADR

Только если одновременно выполнены все условия:

1. Решение дорого откатывать.
2. Без контекста решение будет неочевидным.
3. Был реальный trade-off и выбор из альтернатив.

Если хотя бы одно условие не выполнено, ADR не нужен.

## Копирайт

Адаптировано из
[mattpocock/skills — ADR-FORMAT.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/ADR-FORMAT.md)
(MIT). Каталог: [docs/adr/README.md](../adr/README.md).
Навык: [/explore](../../.cursor/skills/explore/SKILL.md).
