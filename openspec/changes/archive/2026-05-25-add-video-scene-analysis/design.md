## Context

EchoInStone currently processes audio-only content with high accuracy for transcription and speaker diarization. The addition of video scene analysis extends the system to handle visual content, enabling richer analysis of educational videos, presentations, and technical demonstrations. This change introduces computer vision capabilities while maintaining the existing audio processing pipeline.

This updated design also addresses critical issues identified during initial implementation, including OCR configuration problems, PaddleOCR API compatibility issues, insufficient logging for debugging, scattered model storage, and missing scene analysis data in output files.

## Goals / Non-Goals

### Goals
- Enable scene detection and description generation for video files
- Extract text from visual content (code, slides, presentations)
- Integrate video analysis seamlessly with existing audio processing
- Maintain processing performance and accuracy standards
- Provide structured output formats consistent with existing transcription files
- Provide verbose OCR diagnostics to explain empty or low-confidence results

### Non-Goals
- Real-time video processing (focus on batch/offline processing)
- Advanced computer vision tasks (object detection, facial recognition)
- Video editing or manipulation capabilities
- Multi-language OCR beyond English (initial implementation)

## Decisions

### Architecture Pattern
**Decision**: Create MediaProcessingOrchestrator with separate audio and video pipelines

Create a new `MediaProcessingOrchestrator` that coordinates separate `AudioProcessingPipeline` and `VideoProcessingPipeline` components. This maintains Single Responsibility Principle while allowing conditional execution of video analysis.

```python
MediaProcessingOrchestrator
├── AudioProcessingPipeline (always runs)
│   ├── Transcription
│   ├── Diarization
│   └── Alignment
└── VideoProcessingPipeline (conditional)
    ├── Scene Detection
    ├── Description Generation
    └── OCR Text Extraction
```

**Alternatives considered:**
- Extending AudioProcessingOrchestrator: Violates Single Responsibility Principle
- Mandatory video processing: Would break existing audio-only workflows and increase baseline resource usage

### Scene Detection Technology
**Decision**: Use PySceneDetect library for scene boundary detection

PySceneDetect provides reliable scene detection based on visual content changes and histogram analysis. It's lightweight and integrates well with Python ecosystems.

**Alternatives considered:**
- Custom OpenCV implementation: Would require significant development time and tuning
- Deep learning-based scene detection: Too heavy for the current use case and performance requirements

### OCR Technology Selection
**Decision**: Primary Tesseract OCR with PaddleOCR as fallback

Tesseract provides reliable OCR for printed text and code, while PaddleOCR offers better performance for complex layouts. Dual implementation allows quality-based selection with robust error handling and API compatibility fixes.

**Key fixes implemented:**
- Tesseract OCR dependency detection and installation guidance
- PaddleOCR API compatibility handling for 'cls' argument issues
- Robust fallback strategy with comprehensive logging
- Unified model storage location for PaddleX models
- Verbose OCR diagnostics toggle (`OCR_VERBOSE_LOGGING_ENABLED`, enabled by default)
- OCR retry strategies for low-confidence results (preprocessing + parameter variants)

**Alternatives considered:**
- Google Cloud Vision API: External dependency with API costs and rate limits
- AWS Textract: Similar concerns with cloud dependencies
- Single OCR engine: Limits flexibility for different text types

### Output Format Design
**Decision**: JSON format mirroring transcription structure with additional scene metadata

Scene analysis outputs will follow the same directory structure and naming conventions as transcription files, with additional fields for visual content.

```json
{
  "scenes": [
    {
      "id": 1,
      "start_time": 0.0,
      "end_time": 45.2,
      "duration": 45.2,
      "description": "Presentation slide with title and bullet points",
      "extracted_text": "Introduction to Machine Learning\n- Supervised Learning\n- Unsupervised Learning",
      "confidence": 0.85
    }
  ]
}
```

### Save OCR Source Screenshots — Design Details
When OCR is invoked for a scene or detected region, the system SHALL optionally persist the image artifacts used for OCR so that engineers and reviewers can inspect the exact visual input that produced OCR results.

Storage and naming:
- Directory: `<output_root>/<job_id>/ocr_screenshots/<scene_id>/`
- Filenames: `<timestamp>_<engine>_<variant>_<shortid>.png`
  - `timestamp` — ISO8601-like or epoch milliseconds for the frame capture time
  - `engine` — `tesseract` | `paddleocr` | `preprocessed`
  - `variant` — brief descriptor for preprocessing or parameter variant (e.g., `psm3_gray`, `detect_v2`)
  - `shortid` — short stable identifier (e.g., UUID4 truncated) to avoid name collisions

Companion manifest (per job): `<output_root>/<job_id>/ocr_screenshots/manifest.json`
Example manifest entry:

```json
{
  "job_id": "260121_1405_Modus_Dialecticus",
  "images": [
    {
      "filename": "1643200000000_tesseract_psm3_gray_a1b2.png",
      "scene_id": 1,
      "timestamp": 1643200000000,
      "engine": "tesseract",
      "variant": "psm3_gray_v1",
      "preprocessing": ["grayscale","resize_2x"],
      "ocr_confidence": 0.42,
      "text_excerpt": "Introduction to Machine Learning"
    }
  ]
}
```

Configuration:
- `OCR_SAVE_SOURCE_IMAGES_ENABLED` (bool, default: `true`) — master toggle for writing image artifacts
- `OCR_SOURCE_IMAGES_MAX_PER_SCENE` (int, default: 10) — limit images to avoid unbounded disk growth
- `OCR_SOURCE_IMAGE_FORMAT` (string, default: `png`) — image format to write

Integration points:
- Hook into `OCRTextExtractor` implementations to call `data_saver.save_image_artifact()` whenever an image is sent to an OCR engine or to store preprocessed variants
- Ensure `data_saver` writes manifest entries atomically or appends safely to avoid corruption under parallel processing
- Respect configuration toggles before any disk writes

Privacy and disk usage:
- Default behavior is to enable saving (for debugging/QA). For privacy-sensitive deployments, set `OCR_SAVE_SOURCE_IMAGES_ENABLED=false`
- Provide retention guidelines and tools to purge old artifacts (optional maintenance job)

## Risks / Trade-offs

### Performance Impact
**Risk**: Video processing significantly increases computational requirements
**Mitigation**: Implement frame sampling, parallel processing, and optional video analysis

### Accuracy Trade-offs
**Risk**: OCR accuracy may vary with video quality, text size, and font styles
**Mitigation**: Implement confidence scoring, fallback OCR engines, quality preprocessing, and retry strategies with diagnostics

### Dependency Complexity
**Risk**: New computer vision dependencies increase installation complexity
**Mitigation**: Use popular, well-maintained libraries with good Python support and provide comprehensive installation documentation, including Tesseract OCR setup guidance and troubleshooting for common PATH configuration issues

### Memory Usage
**Risk**: Video frame processing requires significant memory for large files
**Mitigation**: Implement streaming processing and frame sampling strategies

## Migration Plan

### Phase 1: Core Implementation
- Implement MediaProcessingOrchestrator with separate pipelines
- Add scene detection and basic description generation
- Implement OCR text extraction with confidence scoring and fallback mechanisms
- Fix PaddleOCR API compatibility issues and add comprehensive logging
- Integrate with existing pipeline as optional feature
- Implement unified model storage for PaddleX models
- Enable verbose OCR diagnostics by default with `OCR_VERBOSE_LOGGING_ENABLED`

### Phase 2: Enhancement
- Add scene-audio timestamp synchronization
- Optimize performance with processing profiles and parallel execution
- Improve OCR accuracy for complex layouts and fallback mechanisms
- Implement comprehensive error handling and progress reporting
- Add OCR retry strategies and diagnostic logging for empty results

### Phase 3: Production Readiness
- Comprehensive testing including visual regression and performance benchmarks
- Model management and update strategies
- Complete documentation, operational runbooks, and user guides

### Rollback Plan
- Video analysis can be disabled via configuration flags
- No changes to existing audio-only processing pipeline
- New dependencies are optional and can be removed if needed

## Open Questions

1. **Video Format Support**: Which video codecs should be prioritized (MP4, WebM, AVI)?
2. **Frame Sampling Strategy**: What sampling rate provides optimal accuracy vs performance balance?
3. **OCR Language Support**: Should we prioritize multi-language OCR from the start?
4. **Storage Requirements**: How should large video files be handled in memory-constrained environments?
5. **Integration Points**: How should video analysis results be correlated with audio transcription timestamps?
6. **Model Management**: How to handle OCR model updates and version compatibility?
7. **Performance Benchmarks**: What are acceptable baseline metrics for video processing performance?