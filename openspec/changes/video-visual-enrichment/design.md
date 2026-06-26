# Design: Video Visual Enrichment

## Context

EchoInStone already has `MediaProcessingOrchestrator`, `VideoProcessingPipeline`,
`PySceneDetectVideoSceneAnalyzer`, and `TesseractOCRTextExtractor` from change
`2026-05-25-add-video-scene-analysis`. That implementation:

- Samples frames mid-scene (not at boundaries)
- Uses `ContentDetector(threshold=27)` — noisy on Jitsi webcam/UI ticks
- Defaults to Tesseract (`OCR_LANGUAGE=en`) with PaddleOCR fallback
- Saves OCR diagnostics to `ocr_screenshots/` but not agent-ready keyframes
- Is disabled via `VIDEO_ANALYSIS_ENABLED = False`

Explore session (2026-06-26) and `C:\!Pavl0\ocr-eval\REPORT.md` established:
EasyOCR `ru`+`en` ~5–10 s/frame on CPU with good webinar UI coverage;
Unlimited-OCR unsuitable for screen capture.

Glossary: [CONTEXT.md](../../../CONTEXT.md).

## Goals / Non-Goals

**Goals:**

- Extract **Keyframes** at meaningful visual moments for lectures/webinars/meetings
- Run **scene-text OCR** (EasyOCR `ru`+`en`) on each keyframe
- Support **two-pass enrichment**: agent supplies timestamps via CLI against an existing job dir
- Produce stable JSON artifacts agents can merge into summaries
- Validate on the Jitsi/Excel reference webinar video

**Non-Goals:**

- Document OCR / PDF parsing (Unlimited-OCR class models)
- Remote OCR APIs or SGLang endpoints
- LLM summarization inside EchoInStone
- PaddleOCR on Windows until stack is fixed (paddle 2.6 or Linux) — deferred
- Real-time / streaming video processing

## Decisions

### 1. Keyframe-centric processing model

**Decision:** Introduce `KeyframeExtractor` as the primary video visual unit; scenes become
optional grouping metadata, not the frame-sampling driver.

**Rationale:** Agents need timestamped PNGs + OCR text, not heuristic scene descriptions alone.

**Alternatives considered:**
- Keep scene-centric sampling — fails at boundary timing (current bug)
- OCR every N seconds only — misses slide changes between intervals without boundary detection

### 2. Combined Trigger strategy

**Decision:** Three trigger types, merged and deduplicated by timestamp (±0.5 s):

| Trigger | Implementation | Default |
|---------|----------------|---------|
| `scene_boundary` | `scenedetect.HashDetector` or SSIM between downscaled frames | threshold tuned on reference video |
| `periodic_fallback` | Every `KEYFRAME_PERIODIC_INTERVAL_SECONDS` | **45 s** |
| `phrase_timestamp` | Parsed from `--extract-at` (pass 2 only) | N/A |

**Rationale:** Hash/SSIM stable on static slides; periodic catches missed transitions;
phrase timestamps enable agent-driven enrichment without full-video OCR.

**Alternatives considered:**
- `ContentDetector` only — rejected (Jitsi noise)
- Periodic only — redundant OCR on static slides

### 3. Scene-text OCR: EasyOCR default

**Decision:** New `EasyOCRTextExtractor` implementing `OCRTextExtractorInterface`;
languages `["ru", "en"]`, `gpu=False` (CPU). Set as default in `VideoProcessingPipeline`
and pass-2 extraction.

**Rationale:** Empirically best on webinar UI (`ocr-eval` §11).

**Alternatives considered:**
- Tesseract default — not installed, weak on ru UI
- Unlimited-OCR — document parser, classifies Excel/chat as `image`
- PaddleOCR eslav — blocked on Windows+paddle 3.3.1

Keep `TesseractOCRTextExtractor` selectable via `OCR_ENGINE` config for environments
with Tesseract installed.

### 4. Keyframe artifact layout

**Decision:**

```
results/{job_id}/
  job_metadata.json          # pass 1: source_video_path, created_at, echo_input
  keyframes/
    manifest.json            # index of all keyframes
    {seconds_ms}_{trigger}_{id}.png
  visual_enrichment.json     # pass 1 full run and/or pass 2 targeted run
  scene_analysis.json        # legacy-compatible scene records (optional, derived)
  speaker_transcriptions.csv # unchanged
```

`manifest.json` entry fields: `id`, `timestamp_seconds`, `trigger`, `image_path`,
`ocr_text`, `ocr_confidence`, `ocr_engine`, `created_at`.

**Rationale:** Agents read one JSON + PNG paths; manifest supports incremental pass-2 adds.

### 5. Two-pass CLI contract

**Decision:**

```bash
# Pass 1 (existing, extended)
echoinstone "path/to/video.mp4" --enable_video_analysis

# Pass 2 (new mode)
echoinstone --job-dir "results/260626_0917_webinar" \
  --extract-at "5:00,12:30,45:00" \
  [--enable_video_analysis]   # implied when --job-dir + --extract-at
```

- `--extract-at` accepts comma-separated `mm:ss`, `hh:mm:ss`, or float seconds
- Pass 2 reads `job_metadata.json` → `source_video_path`; errors if missing
- Pass 2 appends to `keyframes/manifest.json` and merges into `visual_enrichment.json`
- `echo_input` positional arg optional in pass-2 mode

**Rationale:** Agent already has job dir from pass 1 log line.

### 6. Pass 1 job metadata

**Decision:** After video download/processing, write `job_metadata.json`:

```json
{
  "job_id": "260626_0917_webinar",
  "echo_input": "…",
  "source_video_path": "absolute/path/to/video.mp4",
  "video_analysis_enabled": true
}
```

For local file inputs, `source_video_path` is the resolved absolute path.
For remote downloads, use the path returned by the video downloader in the job dir.

### 7. HashDetector vs SSIM

**Decision:** Implement `HashSceneBoundaryDetector` wrapping `scenedetect.HashDetector`
as default; add `SsimKeyframeTrigger` as internal fallback if HashDetector yields
< 2 boundaries on videos > 10 min (configurable `KEYFRAME_MIN_BOUNDARIES`).

**Rationale:** PySceneDetect already a dependency; SSIM fallback cheap to add in-house.

### 8. Dependencies

**Decision:** Add `easyocr` to Poetry **optional extra** `scene-ocr` and document
`poetry install --extras scene-ocr`. `main.py` fails fast with install hint if
video analysis enabled without easyocr.

**Rationale:** EasyOCR pulls torch models (~100 MB); keeps base install lean.

### 9. Re-enable video analysis

**Decision:** Set `VIDEO_ANALYSIS_ENABLED = True` only after integration tests pass
on reference webinar video with non-empty `visual_enrichment.json` OCR text on
at least one Excel-frame timestamp (≥2400 s in reference file).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| EasyOCR typos on small UI text | Return raw text + confidence; agent post-processes |
| Many keyframes on long webinars | Deduplicate triggers; cap `KEYFRAME_MAX_PER_JOB` (default 300) |
| `source_video_path` missing for old jobs | Pass 2 clear error; document re-run pass 1 |
| EasyOCR init ~1–2 s per process | Singleton extractor; reuse in pipeline |
| HashDetector misses soft transitions | `periodic_fallback` at 45 s |
| Disk usage from PNGs | Config `KEYFRAME_SAVE_ENABLED` (default true) |

## Migration Plan

1. Implement `KeyframeExtractor` + `EasyOCRTextExtractor` behind existing interfaces
2. Refactor `VideoProcessingPipeline` to keyframe model; keep `scene_analysis.json` shape
   for backward compatibility where feasible
3. Add pass-2 CLI mode and `job_metadata.json` on pass 1
4. Update `docs/ai/echoinstone-cli.md` and README
5. Validate on reference webinar; then flip `VIDEO_ANALYSIS_ENABLED = True`
6. Rollback: `--disable_video_analysis` and `VIDEO_ANALYSIS_ENABLED = False`

## Open Questions

- Exact `HashDetector` threshold — tune empirically on reference video during implementation
- Whether to copy local video into job dir vs store path only — **default: path only**;
  copy optional via `JOB_COPY_SOURCE_VIDEO = False`
