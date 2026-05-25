# Architecture Decision Records (ADR)

Каталог для коротких записей о необратимых и неочевидных архитектурных решениях.

## Когда появляется первый файл

В режиме [/explore](../../.cursor/skills/explore/SKILL.md) каталог и файлы
создаются **лениво** — только когда одновременно выполнены все критерии из
[ADR-FORMAT.md](../ai/ADR-FORMAT.md)
(дорого откатить, неочевидно без контекста, был реальный trade-off).

До этого момента в репозитории может быть только этот README.

## Именование

`0001-краткий-slug.md`, `0002-...` — следующий номер на единицу больше
максимального в каталоге.

## Шаблон

См. [docs/ai/ADR-FORMAT.md](../ai/ADR-FORMAT.md).

## Происхождение формата

Формат адаптирован из
[grill-with-docs](https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs)
([ADR-FORMAT.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/ADR-FORMAT.md),
MIT).
