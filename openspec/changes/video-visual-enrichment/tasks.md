## 1. Dependencies and Configuration

- [x] 1.1 Add `easyocr` as Poetry optional extra `scene-ocr` in `pyproject.toml`
- [x] 1.2 Add config keys: `KEYFRAME_PERIODIC_INTERVAL_SECONDS` (45), `KEYFRAME_MAX_PER_JOB` (300), `KEYFRAME_DEDUP_SECONDS` (0.5), `OCR_ENGINE` (`easyocr`), `KEYFRAME_SAVE_ENABLED` (true)
- [x] 1.3 Change default `OCR_LANGUAGE` / EasyOCR langs to `ru`+`en` for scene-text OCR
- [x] 1.4 Document `poetry install --extras scene-ocr` in README and `docs/ai/echoinstone-cli.md`

## 2. Keyframe Extraction Core

- [x] 2.1 Create `KeyframeRecord` dataclass and `KeyframeManifest` helper in `EchoInStone/processing/`
- [x] 2.2 Implement `HashSceneBoundaryDetector` (PySceneDetect `HashDetector` wrapper)
- [x] 2.3 Implement `KeyframeExtractor` with combined triggers: `scene_boundary`, `periodic_fallback`, `phrase_timestamp`
- [x] 2.4 Add trigger deduplication (±0.5 s) and `KEYFRAME_MAX_PER_JOB` cap logic
- [x] 2.5 Implement frame capture at trigger timestamps via OpenCV (`cv2.VideoCapture`)

## 3. Scene-text OCR

- [x] 3.1 Implement `EasyOCRTextExtractor` implementing `OCRTextExtractorInterface` (`ru`+`en`, CPU)
- [x] 3.2 Add lazy singleton / model init with clear logging on first use
- [x] 3.3 Wire `OCR_ENGINE` config to select EasyOCR vs Tesseract
- [x] 3.4 Add unit tests for `EasyOCRTextExtractor` with a synthetic image (skip if easyocr not installed)

## 4. Data Saver and Artifacts

- [x] 4.1 Extend `DataSaver` to save keyframe PNGs under `keyframes/`
- [x] 4.2 Implement `save_keyframe_manifest()` and atomic manifest append for pass 2
- [x] 4.3 Implement `save_visual_enrichment()` writing `visual_enrichment.json`
- [x] 4.4 Implement `save_job_metadata()` writing `job_metadata.json` on pass 1
- [x] 4.5 Add tests for manifest merge and deduplication logic

## 5. Pipeline Refactor

- [x] 5.1 Refactor `VideoProcessingPipeline` to use `KeyframeExtractor` + per-keyframe OCR
- [x] 5.2 Map keyframes to `SceneSegment` records for backward-compatible `scene_analysis.json`
- [x] 5.3 Update `MediaProcessingOrchestrator` to pass transcription for correlation (unchanged behavior)
- [x] 5.4 Remove mid-scene-only sampling as primary OCR input strategy

## 6. CLI — Pass 1 Extensions

- [x] 6.1 Write `job_metadata.json` after video download in `main.py`
- [x] 6.2 Ensure local video paths are stored as absolute paths in metadata
- [x] 6.3 Produce `visual_enrichment.json` and `keyframes/manifest.json` on pass 1 when video analysis enabled

## 7. CLI — Pass 2 (Two-pass Enrichment)

- [x] 7.1 Add `--job-dir` and `--extract-at` arguments to `main.py`
- [x] 7.2 Implement pass-2 entry path: load metadata → parse timestamps → extract keyframes → OCR → merge outputs
- [x] 7.3 Make positional `echo_input` optional when `--job-dir` is provided
- [x] 7.4 Add integration test for pass-2 against a fixture job directory

## 8. Testing and Validation

- [x] 8.1 Unit tests for timestamp parsing (`mm:ss`, `hh:mm:ss`, seconds float)
- [x] 8.2 Unit tests for trigger deduplication and max-keyframe cap
- [x] 8.3 BDD scenario: pass 1 video analysis produces non-empty `visual_enrichment.json`
- [ ] 8.4 BDD scenario: pass 2 `--extract-at` appends keyframes to existing job
- [ ] 8.5 Manual validation on reference webinar video (Excel frame ≥2400 s has OCR text)
- [ ] 8.6 Set `VIDEO_ANALYSIS_ENABLED = True` after 8.5 passes

## 9. Documentation

- [x] 9.1 Update `docs/ai/echoinstone-cli.md` with two-pass workflow and output file guide for agents
- [x] 9.2 Update README video analysis section (EasyOCR extra, keyframe outputs)
- [x] 9.3 Update `.cursor/skills/youtube-video-summary/SKILL.md` to mention `visual_enrichment.json` as optional enrichment source
