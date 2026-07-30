# GigaAM hotfix: дедуп overlap и chunk-level сегментация

## Контекст
`EchoInStone/processing/gigaam_audio_transcriber.py`, e2e-прогон YouTube (монолог 757 с)
после архивации change `add-gigaam-xpu-backend`.

## Факт
Первая версия chunked-транскрипции склеивала все слова в один сегмент и дублировала
текст на стыках окон (overlap 5 с): для 12-мин аудио получался 1 ASR-чанк, что обнуляло
диаризацию и таймкоды. После hotfix: 38 ASR-чанков → 11 сегментов спикера в CSV,
границы чистые, остаточное дублирование — единичные слова на отдельных стыках
(артефакт равномерной аппроксимации word timestamps).

## Решение / правило
- Overlap обрезается симметрично: по `(chunk_length - chunk_shift) / 2` с краёв каждого
  окна (кроме краёв аудио).
- Один ASR-чанк на окно транскрипции (не merge всех слов) — SpeakerAligner сам склеит
  соседние чанки одного спикера.
- Точное лечение остаточных дублей — word-level timestamps из lower-level API GigaAM:
  отдельный follow-up change, не hotfix.
- Тесты: pydub замокан в `tests/conftest.py`, поэтому юнит-тесты chunked-логики должны
  патчить `AudioSegment` в модуле транскрайбера фейковым классом, а не реальным pydub.

## Теги
ASR, gigaam, benchmark, pipeline, XPU

## Дата и источник
2026-07-30, ассистент по итогам e2e-прогона https://www.youtube.com/watch?v=VW26WhpwH3s
