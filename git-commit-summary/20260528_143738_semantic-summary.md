# Semantic summary: 20260528_143738

## Контекст

Сессия: обёртки `echoinstone*` в `C:\!Pavl0\.path` (вне репо; правки PS/cmd
и AGENTS.md в `.path` не коммитятся). В репозитории — документация sandbox-run
и исправление ссылок на `sandbox-oneliner` в скиллах.

Продуктового кода (`EchoInStone/`, `tests/`, `features/`) нет.

## Изменения

- **AGENTS.md**: однострочники через `sandbox-run` / sandbox-oneliner; Poetry для кода проекта.
- **.gitignore**: игнор симлинка `.cursor/skills/sandbox-oneliner`.
- **close-chat**, **youtube-video-summary**: пути к sandbox-oneliner → `.cursor/skills/…`.

## Не в коммите

- `C:\!Pavl0\.path\echoinstone*` — локальные PATH-обёртки (отдельный каталог).

## Поведение

- `/close-chat` автокоммит при отсутствии неясностей (этот прогон).
