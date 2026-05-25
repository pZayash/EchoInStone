# Формат CONTEXT

`CONTEXT.md` фиксирует словарь предметной области и связи терминов.
Канон тегов записей [memory/](../../memory/) — отдельно в [TAGS.md](../../TAGS.md)
(не смешивать с `## Language`).

## Когда создавать

- Создавать лениво: только когда появился первый согласованный термин.
- Для single-context проекта: один `CONTEXT.md` в корне.
- Для multi-context проекта: если есть `CONTEXT-MAP.md`, хранить
  `CONTEXT.md` в соответствующем контексте.

## Шаблон

```md
# EchoInStone — домен аудио/видео обработки

Кратко: зачем этот словарь и какая область покрывается.

## Language

**Transcript**:
Текстовое представление речи, полученное ASR-моделью.
_Avoid_: caption (если речь не о субтитрах как артефакте)

**Diarization**:
Разбиение аудио на сегменты по говорящим («кто когда говорил»).
_Avoid_: speaker ID (если не про идентификацию личности)

**Alignment**:
Привязка фрагментов транскрипта к временным меткам и спикерам.
_Avoid_: sync (слишком общее)

## Relationships

- **Transcription** produces a **Transcript**
- **Diarization** segments feed **Alignment**

## Example dialogue

> **Dev:** «После **Diarization** нужен ли отдельный шаг **Alignment**?»
> **Expert:** «Да, Whisper даёт текст, Pyannote — спикеров; aligner склеивает.»

## Flagged ambiguities

- «segment» использовали и для ASR-чанка, и для diarization-интервала —
  развести термины.
```

## Правила

- Выбирать один каноничный термин на понятие.
- Явно фиксировать конфликты терминов в `Flagged ambiguities`.
- Держать определения короткими: одно предложение, «что это», не «что делает».
- Показывать связи между терминами и кардинальность, если она очевидна.
- Включать только доменные понятия, а не общие технические термины (Python, Poetry).
- Добавлять `Example dialogue`, чтобы проверить естественное употребление.

## Multi-context карта

Если контекстов несколько, добавить `CONTEXT-MAP.md` с перечислением
контекстов и связей между ними.

## Копирайт

Адаптировано из
[mattpocock/skills — CONTEXT-FORMAT.md](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/CONTEXT-FORMAT.md)
(MIT). Навык: [/explore](../../.cursor/skills/explore/SKILL.md).
