# Change: Add Video Scene Analysis with OCR Text Extraction and Fixes

## Why

Currently, EchoInStone processes only audio content from video files, extracting transcripts and speaker information. However, video files contain rich visual information that could provide additional context and insights. Users analyzing educational content, presentations, or technical demonstrations would benefit from scene descriptions and automatic text extraction from slides, code examples, or presentation materials.

This proposal addresses both the initial video scene analysis implementation and critical fixes for OCR functionality, logging improvements, and model management issues that were identified during development.

## What Changes

### New Video Scene Analysis Features
- **NEW**: Add video scene analysis capability that breaks video files into distinct scenes
- **NEW**: Generate scene description files with timestamps, similar to transcription output
- **NEW**: Extract text from scenes containing textual content (code demos, presentations, slides)
- **NEW**: Integrate scene analysis into the existing audio processing pipeline
- Extend supported input sources to include video files for scene analysis
- **CHANGE**: Enable video scene analysis by default, with configuration to disable it

### OCR Source Image Artifacts
- **NEW**: Save OCR source images (original frames and any preprocessed variants) used for OCR attempts to the processing output directory for post-hoc analysis
- **NEW**: Add configuration key `OCR_SAVE_SOURCE_IMAGES_ENABLED` (default: `true`) to control saving of OCR image artifacts
- **NEW**: Produce a companion JSON manifest per job that links saved images to scene ids, timestamps, OCR engine attempts, preprocessing steps, and confidence summaries

### OCR Configuration and Bug Fixes
- **FIX**: Resolve Tesseract OCR installation and PATH configuration issues
- **FIX**: Fix PaddleOCR API compatibility issues with 'cls' argument errors
- **ENHANCE**: Add comprehensive logging for PySceneDetect scene detection process
- **ENHANCE**: Add verbose OCR diagnostics (per-engine results, thresholds, region stats)
- **ENHANCE**: Add config key to enable/disable verbose OCR logging (default on)
- **FIX**: Standardize PaddleX model storage location to match Whisper and other AI models
- **FIX**: Ensure scene analysis results are properly saved to output files
- **ENHANCE**: Implement robust OCR fallback strategy with proper error handling
- **ENHANCE**: Add OCR quality improvement retries (preprocessing, psm/oem variants)

## Impact

- **Affected specs**: Updates `video-scene-analysis` capability with OCR diagnostics and defaults
- **Affected code**: New `processing/video_scene_analyzer.py`, `processing/ocr_text_extractor.py` modules with fixes
- **Affected architecture**: Creates new `MediaProcessingOrchestrator` coordinating separate audio and video pipelines
- **New dependencies**: Computer vision libraries (OpenCV, scenedetect, OCR libraries like Tesseract/PaddleOCR)
- **Data output**: New JSON files with scene metadata, extracted text, and synchronization data alongside existing transcription files
- **System requirements**: Tesseract OCR installation for OCR functionality
- **Model storage**: Unified model directory structure for consistent AI model management