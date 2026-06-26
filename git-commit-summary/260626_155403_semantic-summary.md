# Semantic summary: 260626_155403

## Контекст

Сессия: реализация change `video-visual-enrichment` — keyframe extraction, EasyOCR scene-text,
two-pass CLI (`--job-dir` + `--extract-at`) для обогащения суммаризаций визуальным контентом
вебинаров/лекций. Ручная валидация на Excel-семинаре Jitsi (pass 1 + pass 2 OCR).

## Изменения

- **EchoInStone/processing/**: `KeyframeExtractor`, `HashSceneBoundaryDetector`, `KeyframeRecord`,
  `EasyOCRTextExtractor`, `ocr_factory`, `timestamp_parser`; рефактор `VideoProcessingPipeline`
- **main.py**: pass 2 entry (`--job-dir`, `--extract-at`), `job_metadata.json` на pass 1
- **EchoInStone/utils/data_saver.py**: `visual_enrichment.json`, keyframe manifest, PNG save
- **EchoInStone/config.py**: OCR/keyframe keys; `VIDEO_ANALYSIS_ENABLED = False` до task 8.6
- **pyproject.toml / poetry.lock**: optional extra `scene-ocr` (easyocr)
- **tests/**: unit + integration для parser, keyframes, EasyOCR mock, pass-2 CLI
- **features/steps/test_video_scene_analysis_bdd.py**: fix dummy pipeline return tuple
- **docs**: README, `echoinstone-cli.md`, youtube-video-summary skill
- **openspec/changes/video-visual-enrichment/**: proposal, design, specs, tasks (35/38 done)
- **CONTEXT.md**: доменный словарь и agreed decisions explore-сессии

## Технические детали

- Triggers: `scene_boundary` (hash) + `periodic_fallback` (45s) + `phrase_timestamp`
- OCR default: EasyOCR `ru`+`en`, CPU; Unlimited-OCR отклонён после ocr-eval
- Pass 2 merge: append keyframes + OCR в существующий job dir без полного re-run

## Не вошло в коммит

- `results/**` — артефакты прогона (транскрипт, keyframes, summary_enriched.md)
- `diarization/`, медиафайлы, секреты

## Поведение / UX

```bash
# Pass 1
echoinstone "<video>" --enable_video_analysis

# Pass 2
echoinstone --job-dir "results/<job_id>" --extract-at "mm:ss,…"
```

## OpenSpec

- Change `video-visual-enrichment` in-progress: tasks 8.4–8.6 открыты (BDD pass-2, flip default flag)
- Archive отложен до закрытия задач
