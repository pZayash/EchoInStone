# Change: Video Visual Enrichment for Summary Augmentation

## Why

EchoInStone summaries are built only from audio transcripts. The existing video scene
analysis pipeline (PySceneDetect + Tesseract) does not produce usable on-screen text:
`VIDEO_ANALYSIS_ENABLED` is off, Tesseract is often missing, `ContentDetector` is noisy
on Jitsi webinar recordings, and Russian UI text is not recognized. Agents summarizing
lectures, webinars, and meetings need **Keyframes** with **scene-text OCR** to enrich
summaries with what appears on screen (slides, Excel, chat).

Empirical evaluation (`C:\!Pavl0\ocr-eval\REPORT.md`, 2026-06-26) confirmed EasyOCR
(`ru`+`en`) works for webinar UI; `baidu/Unlimited-OCR` is unsuitable for screen capture.

## What Changes

- **NEW**: `KeyframeExtractor` with combined **Triggers**: `scene_boundary` (hash/SSIM),
  `periodic_fallback` (default 45 s), `phrase_timestamp` (agent-driven)
- **NEW**: First-class **Keyframe** artifacts (`keyframes/` + `keyframes/manifest.json`)
  distinct from diagnostic `ocr_screenshots/`
- **NEW**: `EasyOCRTextExtractor` as default **scene-text OCR** (`ru`+`en`, CPU)
- **CHANGE**: Replace `ContentDetector`-only scene boundaries with hash/SSIM detector
  tuned for screen-share webinars
- **NEW**: Pass 1 writes `job_metadata.json` with `source_video_path` for pass 2
- **NEW**: Two-pass CLI: `--job-dir <results/…/>` + `--extract-at "mm:ss,…"` →
  `visual_enrichment.json` in the same job directory
- **CHANGE**: Refactor `VideoProcessingPipeline` to extract keyframes at trigger points
  (not mid-scene sampling) and run OCR per keyframe
- **CHANGE**: Default OCR language config to bilingual `ru`+`en` for scene-text OCR
- **CHANGE**: Re-enable `VIDEO_ANALYSIS_ENABLED` after validation on reference webinar video
- **KEEP**: `TesseractOCRTextExtractor` as optional fallback extractor (not default)
- **OUT OF SCOPE**: `baidu/Unlimited-OCR`, remote OCR endpoints, in-pipeline LLM summarization

## Capabilities

### New Capabilities

- `keyframe-extraction`: Trigger-based keyframe capture, deduplication, manifest, periodic fallback
- `visual-enrichment-cli`: Two-pass enrichment CLI (`--job-dir`, `--extract-at`), job metadata, output contract for agents

### Modified Capabilities

- `video-scene-analysis`: Scene boundary detection strategy, scene-text OCR default engine,
  keyframe-centric processing model, `visual_enrichment.json` output, job metadata on pass 1

## Impact

- **Affected code**: `EchoInStone/processing/` (new extractor, OCR impl, pipeline refactor),
  `EchoInStone/utils/data_saver.py`, `main.py`, `EchoInStone/config.py`
- **New dependencies**: `easyocr` (Poetry main or optional extra — see design.md)
- **CLI**: New flags `--job-dir`, `--extract-at`; updated `docs/ai/echoinstone-cli.md`
- **Output layout**: `keyframes/`, `keyframes/manifest.json`, `visual_enrichment.json`,
  `job_metadata.json` under `results/{job_id}/`
- **Tests**: `tests/`, `features/` for keyframe extraction, EasyOCR, two-pass CLI
- **Reference video**: `.tmp/ОбучениеЭксель2026/10.06.26/1.1) …Jitsi Meet….mp4`
- **Domain glossary**: [CONTEXT.md](../../../CONTEXT.md)
