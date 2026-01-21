# Change: Add Video Scene Analysis with OCR Text Extraction

## Why

Currently, EchoInStone processes only audio content from video files, extracting transcripts and speaker information. However, video files contain rich visual information that could provide additional context and insights. Users analyzing educational content, presentations, or technical demonstrations would benefit from scene descriptions and automatic text extraction from slides, code examples, or presentation materials.

## What Changes

- **NEW**: Add video scene analysis capability that breaks video files into distinct scenes
- **NEW**: Generate scene description files with timestamps, similar to transcription output
- **NEW**: Extract text from scenes containing textual content (code demos, presentations, slides)
- **NEW**: Integrate scene analysis into the existing audio processing pipeline
- Extend supported input sources to include video files for scene analysis

## Impact

- **Affected specs**: Creates new `video-scene-analysis` capability
- **Affected code**: New `processing/video_scene_analyzer.py`, `processing/ocr_text_extractor.py` modules
- **Affected architecture**: Creates new `MediaProcessingOrchestrator` coordinating separate audio and video pipelines
- **New dependencies**: Computer vision libraries (OpenCV, scenedetect, OCR libraries like Tesseract/PaddleOCR)
- **Data output**: New JSON files with scene metadata, extracted text, and synchronization data alongside existing transcription files