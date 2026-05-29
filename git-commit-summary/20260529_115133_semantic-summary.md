# Semantic summary: 20260529_115133

## Контекст

Сессия: резюме YouTube (Кормачев, data-driven BA), уточнение workflow
(чтение CSV из `results/` без `export_diarized_txt.py`, sandbox через `-Files`).
Закрытие: коммит только правок навыка `/youtube-summary`.

## Изменения

- **youtube-video-summary**: обязательный блок «Вопросы для углубления» (4–6,
  NotebookLM-style) в конце ответа и опционально в `summary.md`; правила типов
  вопросов; follow-up по выбранному вопросу без перегенерации резюме.
- **youtube-summary** (команда): напоминание про блок вопросов в конце ответа.

## Не вошло в коммит

- `results/**` — транскрипт и `summary.md` ролика `-jgF--8HxSo` (локальные артефакты).
- `memory.md` (untracked) — шаблон долговременных правил, пустой; не часть этой правки.
- Остальной diff ветки `pzayash` vs `main` (workflow explore/close-chat и др.) — вне touched этой сессии.

## OpenSpec

- Активных changes нет (`openspec list` → `[]`). Archive не требовался.
