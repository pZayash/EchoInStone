# EchoInStone — домен аудио/видео обработки

Кратко: каноничная лексика домена (ASR, диаризация, визуальное обогащение). Исторически наполнялся для change «video-visual-enrichment»; с 2026-07-29 — также для трека optional GigaAM backend. Канон тегов записей `memory/` — в [TAGS.md](TAGS.md), не здесь.

## Language

**ASR chunk** _(согласовано, 2026-07-29)_:
Элемент выхода ASR для **Alignment**: объект с интервалом `(start, end)` и текстом; список таких элементов потребляет `SpeakerAligner`.
_Avoid_: «word» (более мелкий уровень GigaAM до склейки); «engine segment» / термин zapis; «subtitle cue» (артефакт экспорта, change 2).

**GigaAM backend** _(согласовано, 2026-07-29)_:
Опциональный **transcriber backend** (`gigaam`): ASR на базе GigaAM v3 CTC (+ опционально KenLM), после adapter отдаёт те же **ASR chunk**, что Whisper-бэкенды.
_Avoid_: «engine» (лексика zapis); путать с отдельным OpenVINO/NPU-портом сторонних проектов.

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

- **GigaAM backend** produces **ASR chunk**-s (via words→chunks adapter)
- Whisper backends also produce **ASR chunk**-s → **Alignment** / diarization
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

## Agreed decisions (explore 2026-07-29, zapis → EchoInStone)

| Решение | Выбор |
|---------|--------|
| Delivery model | **H2**: три отдельных OpenSpec change подряд |
| Change 1 scope | Только optional **GigaAM** as transcriber backend; adapter → существующий формат ASR chunk; без SRT/VTT и без LLM |
| Dependencies | Poetry extra (как `faster-whisper`), не core |
| Isolation | Новый change, не смешивать с `video-visual-enrichment` |
| Later (out of change 1) | Change 2: subtitle export; Change 3: LLM-пресеты |
| KenLM | Change 1 — **не включать** (только greedy). Опция «есть → LM» отложена в follow-up |
| Лексика | **ASR chunk**, **GigaAM backend** (не «engine») |
| Auto + язык | Auto → GigaAM при детекте `ru` через **Whisper tiny** на первых ~30 s |
| Детект: порог | Детект только если длительность > ~10 s; иначе — без детекта (текущий auto) |
| Детект ≠ ru | Fallback на текущий auto (Whisper-путь) |
| Device | Intel XPU: **PASS** (spike 2026-07-30). Fail → отложить |
| Longform strategy | **Без** `gigaam[longform]` extra: чанкинг на стороне EchoInStone + per-chunk `transcribe()` (~≤25 s); zapis LongformCTC/KenLM-merge не переносим |
| OpenVINO GigaAM | Вне change 1 |
| Scope change 1 | CLI + auto-pick по детекту `ru` |
| Spike artifacts | Оставить до конца proposal; venv потом удалить, REPORT.md оставить |
| Бенч в change 1 | `results_test/`: ru-фикстура + сравнение GigaAM vs Whisper (качество, время) |

## Empirical notes (2026-07-30, `results_test/gigaam_xpu_spike/REPORT.md`)

- XPU smoke **PASS**: `gigaam.load_model("v3_ctc", device="xpu")` нативно, Arc 140T, fp16; transcript == CPU; warm ~40x realtime на 15 s клипе.
- Side-venv + `.pth` bridge → poetry env не тронут, CUDA-torch не подтягивается.
- Блокер: extra `gigaam[longform]` пинит `torch==2.10.*`, `pyannote.audio==4.0.*`, `transformers==5.*` — конфликт с проектом; longform делать без этого extra (chunking/своя сегментация).
- Known warning: `_VF.stft` fallback XPU→CPU (не блокирует корректность).

- `baidu/Unlimited-OCR`: XPU работает после патча `.cuda()` → `.to(device)`; ~24 s/frame на Arc 140T; **не читает** chat/Excel/календарь (классифицирует как `image`). **Не default.**
- EasyOCR (`ru`+`en`, CPU): ~5–10 s/frame; читает ribbon, ячейки, чат (с типичными опечатками). **Default.**
- PaddleOCR (`eslav`, CPU): падает на Windows+paddle 3.3.1 (oneDNN); нужен downgrade или Linux — **отложено.**

## Flagged ambiguities

- В существующем коде `SceneSegment` (интервал между границами) и «scene» как событие границы смешаны. Канон: **SceneSegment** = интервал; событие границы = **Trigger** типа `scene_boundary`.
- «скриншот» (пользовательский термин) = **Keyframe**; не использовать «screenshot» в коде/спеках.
- «Русский язык» для auto-select **GigaAM backend**: согласован **автодетект** лёгкой моделью (не только явный CLI). Конкретный детектор — не выбран.
- GigaAM upstream/zapis: device `cuda`|`cpu` only; но spike показал `xpu` работает. Осталась неоднозначность **KenLM на Windows+XPU** (не проверялся в smoke) — только greedy тестировался.
