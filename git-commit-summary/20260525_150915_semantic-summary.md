# Semantic summary: 20260525_150915

## Контекст

Перенос и адаптация AI-workflow из проекта КПСР UNF 2020 в EchoInStone:
режим исследования `/explore` (grill-with-docs + CONTEXT/ADR) и закрытие сессии
`/close-chat` с коммитом только touched-файлов.

Изменений продуктового кода (`EchoInStone/`, `tests/`, `features/`) в этом batch нет.

## Изменения

- **explore**: навык и команды `/explore`, `/opsx-explore` (алиас); форматы `CONTEXT.md`,
  `docs/adr/`, `memory/`, `TAGS.md`.
- **close-chat**: четырёхшаговый пайплайн (вопросы → archive OpenSpec → очистка → коммит);
  команда `/git-summarize-and-commit` для EchoInStone.
- **openspec-explore**: сведён к алиасу на `explore`.
- **AGENTS.md**, **openspec/changes/README.md**: описание workflow для агентов.
- **memory/feedback_openspec_always_sync_and_archive.md**: sync delta-spec перед archive по умолчанию.
- **docs/ai/openspec-implementation-notes.md**: журнал отклонений при apply.

## Технические детали

- `.claude/commands` и `.claude/skills` остаются в `.gitignore` (junction на `.cursor`).
- close-chat не трогает `results/**`; коммиты только с явного подтверждения пользователя.
- explore запрещает правки `EchoInStone/**` в режиме исследования.

## Поведение / UX CLI

Новые slash-команды: `/explore`, `/close-chat`, `/git-summarize-and-commit`.
