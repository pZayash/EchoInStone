---
name: close-chat
description: >-
  Автокоммит touched-файлов сессии, если нет неясностей; иначе — отчёт и
  вопросы. Перед коммитом: archive готовых OpenSpec, лёгкая очистка. Триггеры:
  /close-chat, «закрыть чат», «заверши сессию».
argument-hint: "--dry-run | --skip 0|1|2|3 (опционально)"
---

# close-chat — автокоммит в конце сессии

**Назначение:** по команде `/close-chat` **самому закоммитить** изменения сессии, если всё однозначно. Не ждать отдельного «коммить».

Аргументы: `--dry-run` (шаги без `git commit`), `--skip N` (пропустить шаги 0–3).

## Решение: коммитить или нет

**Автокоммит**, если одновременно:

- нет открытых вопросов к пользователю и нет блокеров;
- понятно, **какие файлы** входят в коммит (touched за сессию, без `diarization/`, `results/`, секретов, бинарников);
- нет спорных OpenSpec changes без выбора пользователя (см. шаг 1);
- не `--dry-run`.

**Только отчёт** (без коммита), если:

- нужен выбор пользователя (scope, archive, удаление файлов);
- в diff есть подозрение на секреты;
- нет изменений для коммита.

Вызов `/close-chat` = согласие на коммит **при выполнении условий выше**. Иначе — явно написать, что мешает.

## Шаг 0 — Гейт неясностей

- Собрать незакрытые вопросы и блокеры.
- Прочитать `openspec/changes/*/implementation-notes.md` (если есть).
- Если гейт не пройден → **стоп**, отчёт, **без коммита**.

## Шаг 1 — OpenSpec (кратко)

`openspec` — **без Poetry**, из корня репозитория. Запасной вариант: `sandbox-run` + `openspec list --json` ([sandbox-oneliner](~/.claude/skills/sandbox-oneliner/)); archive — на хосте (нужен git).

- `openspec list --json` — активные changes.
- Готовый change без неясностей → [openspec-archive-change](../openspec-archive-change/SKILL.md) (sync delta, `openspec archive <name> -y`).
- Несколько changes или незавершённые артефакты → **не угадывать**; спросить или пропустить archive.

## Шаг 2 — Очистка

- Убрать явный мусор сессии (пустые черновики, дубликаты).
- **Не удалять** без спроса: `results/**`, `diarization/**`.
- `implementation-notes.md` — удалить после archive по openspec-archive-change.

## Шаг 3 — Автокоммит (главный шаг)

1. `git status` / `git diff` — только **touched** сессии.
2. **Исключить:** `diarization/`, `results/`, `*.log`, медиа, `EchoInStone/config_private.py`, секреты.
3. `git add` выбранные пути.
4. Сообщение коммита: Conventional Commits, «why» в теле при необходимости.
5. Записать `git-commit-summary/YYMMDD_HHMMSS_semantic-summary.md` (контекст, список изменений, что не вошло).
6. `git commit` (HEREDOC). После hook — новый коммит, не amend, если hook менял файлы.
7. `git status` — подтвердить успех.

Шаблон summary — см. `git-commit-summary/20260525_150915_semantic-summary.md`.

## Отчёт пользователю

- Прошёл ли гейт; что в коммите (hash, subject); что осталось untracked и почему.
- Если коммита не было — одна причина и что нужно от пользователя.
