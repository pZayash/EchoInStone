# EchoInStone — домен аудио/видео обработки

Кратко: словарь для change'а «обогащение суммаризаций визуальным контентом видео» (лекции, вебинары, встречи). Канон тегов записей `memory/` — в [TAGS.md](TAGS.md), не здесь.

## Language

**Keyframe**:
Кадр видео, извлечённый в момент срабатывания **Trigger** и сохранённый как first-class артефакт (PNG + запись в манифесте), пригодный для OCR и выдачи агенту.
_Avoid_: «screenshot» (бытовой), «sampled frame» / «OCR source image» (старые термины из `video_processing_pipeline.py` — там это диагностический побочный продукт OCR, не самостоятельный артефакт).

**Trigger**:
Событие, вызывающее извлечение **Keyframe**. Каноничные подтипы (согласовано):
- `scene_boundary` — визуальная смена screen-share (HashDetector / SSIM, не ContentDetector для Jitsi);
- `periodic_fallback` — фолбэк по таймеру (дефолтный интервал уточняется в design, ориентир 30–60 с);
- `phrase_timestamp` — точечная метка из транскрипта, переданная агентом во **two-pass** CLI.
_Avoid_: «scene» (перегружено: сцена = интервал между границами, а не само событие); «keypoint» (размыто).

**Two-pass enrichment**:
Сценарий: проход 1 — аудио-суммаризация (существующий); проход 2 — агент вызывает CLI с `--job-dir` (каталог pass 1) и `--extract-at` (список меток), получает **Keyframe**-ы и `visual_enrichment.json`, обогащает суммаризацию.
_Avoid_: «re-run» (не весь пайплайн, а точечный запрос); повторная передача пути к видео, если job dir уже известен.

**Scene-text OCR**:
OCR для плотных UI-скриншотов (вебинар, Jitsi, Excel/Word в screen-share, чат): детектор текстовых регионов + распознавание по регионам.
_Avoid_: «document parsing» (класс моделей вроде Unlimited-OCR, заточенных под PDF/страницы).

**Document OCR**:
OCR для цельных документов/страниц (PDF, слайды как отдельные страницы), часто через VLM с layout-токенами (`<|det|>…`).
_Avoid_: использовать как default для webinar screen capture — empirically weak (см. `C:\!Pavl0\ocr-eval\REPORT.md`).

## Relationships

- **Trigger** produces one **Keyframe**
- **Two-pass enrichment** consumes **Keyframe**-s on pass 2 (тип **Trigger**: `phrase_timestamp`)
- **Keyframe** is input to **Scene-text OCR** (`OCRTextExtractorInterface`)

## Agreed decisions (explore 2026-06-26)

| Решение | Выбор |
|---------|--------|
| Scope change | Все 3 слоя: KeyframeExtractor + Scene-text OCR + two-pass CLI |
| OCR default | EasyOCR (`ru`+`en`, CPU); Unlimited-OCR — не включать |
| Trigger strategy | Комбинированная: `scene_boundary` (hash) + `periodic_fallback` + `phrase_timestamp` |
| Two-pass CLI | `--job-dir <results/…/>` + `--extract-at "mm:ss,…"`; выход в тот же job dir: `keyframes/` + `visual_enrichment.json` |

## Empirical notes (2026-06-26, `C:\!Pavl0\ocr-eval`)

- `baidu/Unlimited-OCR`: XPU работает после патча `.cuda()` → `.to(device)`; ~24 s/frame на Arc 140T; **не читает** chat/Excel/календарь (классифицирует как `image`). **Не default.**
- EasyOCR (`ru`+`en`, CPU): ~5–10 s/frame; читает ribbon, ячейки, чат (с типичными опечатками). **Default.**
- PaddleOCR (`eslav`, CPU): падает на Windows+paddle 3.3.1 (oneDNN); нужен downgrade или Linux — **отложено.**

## Flagged ambiguities

- В существующем коде `SceneSegment` (интервал между границами) и «scene» как событие границы смешаны. Канон: **SceneSegment** = интервал; событие границы = **Trigger** типа `scene_boundary`.
- «скриншот» (пользовательский термин) = **Keyframe**; не использовать «screenshot» в коде/спеках.
