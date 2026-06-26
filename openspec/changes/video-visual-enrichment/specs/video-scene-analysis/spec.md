## ADDED Requirements

### Requirement: Scene-text OCR with EasyOCR default
The system SHALL use a scene-text OCR engine optimized for UI screenshots as the default
OCR implementation for keyframe processing, with Russian and English language support.

#### Scenario: EasyOCR default on keyframes
- **WHEN** a keyframe is processed for text extraction and `OCR_ENGINE` is not set to an alternative
- **THEN** the system uses EasyOCR with languages `ru` and `en`
- **AND** returns extracted text with per-keyframe confidence and engine name `easyocr`

#### Scenario: EasyOCR missing dependency
- **WHEN** video analysis is enabled and EasyOCR is not installed
- **THEN** the system logs an error with installation instructions (`poetry install --extras scene-ocr`)
- **AND** continues audio processing without crashing the full job

#### Scenario: Optional Tesseract engine
- **WHEN** `OCR_ENGINE` is set to `tesseract` and Tesseract is available
- **THEN** the system uses `TesseractOCRTextExtractor` instead of EasyOCR
- **AND** logs which engine is active

### Requirement: Visual enrichment JSON output
The system SHALL produce `visual_enrichment.json` alongside legacy scene outputs when
full video visual analysis runs on pass 1.

#### Scenario: Pass-1 visual enrichment file
- **WHEN** pass 1 completes with `--enable_video_analysis`
- **THEN** the system writes `<job_dir>/visual_enrichment.json` containing all keyframe OCR results
- **AND** writes `<job_dir>/keyframes/manifest.json`

#### Scenario: Legacy scene analysis compatibility
- **WHEN** `scene_analysis.json` is still produced
- **THEN** scene records reference keyframe OCR results where applicable
- **AND** include `extracted_text`, `ocr_confidence`, and `ocr_engine` from the keyframe at the scene start

## MODIFIED Requirements

### Requirement: Video Scene Detection
The system SHALL analyze video files and detect visual change boundaries suitable for
screen-share webinar content using hash or SSIM-based detection, in addition to or
instead of content-histogram detection.

#### Scenario: Scene boundary detection
- **WHEN** a video file is processed with visual analysis enabled
- **THEN** the system identifies visual change boundaries using a hash or SSIM-based detector by default
- **AND** each boundary has a timestamp used for keyframe extraction
- **AND** each scene interval has start and end timestamps

#### Scenario: Scene metadata generation
- **WHEN** scenes are detected
- **THEN** the system generates scene metadata including duration and frame count
- **AND** metadata is saved in JSON format alongside transcription files

### Requirement: Text Extraction from Visual Content
The system SHALL detect and extract on-screen text from keyframes at trigger timestamps
for scenes containing textual information such as presentations, application UIs, slides,
code demonstrations, or chat panels.

#### Scenario: Text content detection
- **WHEN** a keyframe contains visible text (slides, application UI, chat, presentations)
- **THEN** the system runs scene-text OCR on the keyframe image
- **AND** associates extracted text with the keyframe timestamp

#### Scenario: OCR text extraction
- **WHEN** scene-text OCR processes a keyframe
- **THEN** the system extracts readable text using the configured OCR engine (EasyOCR by default)
- **AND** associates extracted text with the corresponding timestamp in `visual_enrichment.json`

#### Scenario: Mixed content handling
- **WHEN** a scene contains both visual elements and on-screen text
- **THEN** the system provides scene descriptions (where generated) and OCR-extracted text from keyframes
- **AND** clearly differentiates descriptive text from OCR-extracted text in output fields

### Requirement: Video Analysis Configuration
The system SHALL provide configurable options to enable or disable video visual analysis
via `VIDEO_ANALYSIS_ENABLED`, and video analysis SHALL be enabled by default once this
change is validated on the reference webinar video.

#### Scenario: Configuration file control
- **WHEN** a configuration file is present
- **THEN** the system reads video analysis settings from the configuration file
- **AND** enables or disables video visual analysis based on the configuration

#### Scenario: Command-line parameter control
- **WHEN** command-line arguments are provided
- **THEN** the system accepts parameters to enable/disable video analysis
- **AND** command-line options override configuration file settings for pass 1

#### Scenario: Default behavior after validation
- **WHEN** no configuration override is specified after this change ships
- **THEN** `VIDEO_ANALYSIS_ENABLED` defaults to `true`
- **AND** users can explicitly disable video analysis with `--disable_video_analysis`
