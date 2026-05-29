---
name: git-summarize-and-commit
description: >-
  Семантический summary staged изменений и git commit (EchoInStone).
  Conventional Commits + запись в git-commit-summary/*.md. Триггеры:
  /git-summarize-and-commit, «коммить staged», «semantic commit».
argument-hint: "(опционально) scope или подсказка для сообщения коммита"
---

# git-summarize-and-commit — semantic summary + commit

**Назначение:** по `/git-summarize-and-commit` проанализировать изменения, записать
семантический summary в `git-commit-summary/` и создать git-коммит. Используется
напрямую или из шага 3 навыка [close-chat](../close-chat/SKILL.md).

Вызов команды = явное разрешение на коммит (вне `/close-chat` коммиты иначе только
по прямому запросу пользователя).

## Предусловия

**Стоп без коммита**, если:

- нет изменений для коммита (ни staged, ни однозначного набора для stage);
- в diff подозрение на секреты (`.env`, токены, `config_private.py`);
- неясно, какие файлы включать — спросить пользователя.

## Шаг 1 — Сбор состояния

Параллельно:

```bash
git status
git diff --staged
git diff
git log -5 --oneline
```

Если **ничего не staged**:

- при вызове из **close-chat** — stage только **touched** за сессию (см. исключения ниже);
- при прямом вызове — stage только если scope однозначен; иначе отчёт и вопрос.

## Шаг 2 — Исключения (EchoInStone)

**Не включать** в коммит без явного запроса:

- `diarization/`, `results/`, `*.log`, медиафайлы;
- `EchoInStone/config_private.py`, секреты, `.env`;
- артефакты, не относящиеся к задаче сессии.

## Шаг 3 — Semantic summary

Записать `git-commit-summary/YYMMDD_HHMMSS_semantic-summary.md` (локальное время).

Шаблон секций (адаптировать по смыслу diff):

```markdown
# Semantic summary: YYMMDD_HHMMSS

## Контекст
<зачем batch, что за сессия; есть ли продуктовый код>

## Изменения
<группы по темам/компонентам, bullet list>

## Технические детали
<неочевидные решения, ограничения — опционально>

## Не вошло в коммит
<исключённые пути и почему — опционально>

## Поведение / UX
<если меняется CLI, навыки, workflow — опционально>

## OpenSpec
<активные/archived changes, если релевантно — опционально>
```

Образец: `git-commit-summary/20260525_150915_semantic-summary.md`.

Summary пишется **до** `git commit`, но описывает тот же набор файлов, что войдёт в коммит
(включая сам файл summary, если он добавляется в тот же commit).

## Шаг 4 — Stage и commit

1. `git add` выбранные пути (summary + изменения).
2. Сообщение: **Conventional Commits** (`feat:`, `fix:`, `docs:`, `chore:` …), subject ≤72 символов;
   тело — «why», если неочевидно из subject.
3. Commit через HEREDOC:

```bash
git commit -m "$(cat <<'EOF'
subject line

Optional body explaining why.
EOF
)"
```

4. Hook изменил файлы после commit → **новый** commit, не `--amend` (если HEAD не ваш или уже pushed).
5. `git status` — подтвердить успех.

## Git safety

- Не менять `git config`, не `--no-verify`, не force-push.
- Не коммитить файлы с секретами; предупредить пользователя.
- Пустой коммит не создавать.

## Отчёт пользователю

- Hash и subject коммита.
- Путь к semantic summary.
- Что осталось unstaged/untracked и почему.
- Если коммита не было — одна причина и что нужно от пользователя.
