## ADDED Requirements

### Requirement: Video Scene Detection
The system SHALL analyze video files and automatically detect scene boundaries based on visual content changes.

#### Scenario: Scene boundary detection
- **WHEN** a video file is processed
- **THEN** the system identifies distinct scenes based on visual transitions
- **AND** each scene has start and end timestamps

#### Scenario: Scene metadata generation
- **WHEN** scenes are detected
- **THEN** the system generates scene metadata including duration and frame count
- **AND** metadata is saved in JSON format alongside transcription files

### Requirement: Scene Description Generation
The system SHALL generate descriptive text for each detected scene using computer vision analysis.

#### Scenario: Scene content analysis
- **WHEN** a scene is detected
- **THEN** the system analyzes visual content to generate scene descriptions
- **AND** descriptions include key visual elements and activities

#### Scenario: Scene description output
- **WHEN** scene descriptions are generated
- **THEN** they are saved in a structured format with timestamps
- **AND** the output file follows the same naming convention as transcription files

### Requirement: Text Extraction from Visual Content
The system SHALL detect and extract text from scenes containing textual information such as code demonstrations, presentations, or slides.

#### Scenario: Text content detection
- **WHEN** a scene contains visible text (code, slides, presentations)
- **THEN** the system identifies the presence of textual content
- **AND** triggers OCR (Optical Character Recognition) processing

#### Scenario: OCR text extraction
- **WHEN** textual content is detected in a scene
- **THEN** the system extracts readable text using OCR technology
- **AND** associates extracted text with the corresponding scene timestamps

#### Scenario: Mixed content handling
- **WHEN** a scene contains both visual elements and text
- **THEN** the system provides both scene descriptions and extracted text
- **AND** clearly differentiates between descriptive text and OCR-extracted text

### Requirement: Video Processing Integration
The system SHALL integrate video scene analysis into the existing audio processing pipeline using a unified orchestrator.

#### Scenario: Unified processing workflow
- **WHEN** a video file is provided as input
- **THEN** the system processes both audio and video content through coordinated pipelines
- **AND** generates synchronized audio transcripts and scene analysis outputs

#### Scenario: Output file organization
- **WHEN** processing completes
- **THEN** all output files (transcription, scenes, OCR text) are saved in the same output directory
- **AND** files follow consistent naming patterns for easy correlation

#### Scenario: Scene-audio synchronization
- **WHEN** video scenes and audio transcription are processed
- **THEN** the system aligns scene timestamps with transcription segments
- **AND** correlates visual content changes with speaker transitions

#### Scenario: Multi-modal correlation
- **WHEN** OCR text is extracted from scenes
- **THEN** the system attempts to correlate extracted text with audio transcription content
- **AND** provides confidence scores for text-audio alignment

### Requirement: OCR Configuration and Setup
The system SHALL provide clear configuration management and setup guidance for OCR functionality, including automated dependency detection and installation prompts.

#### Scenario: Tesseract OCR dependency detection
- **WHEN** the system attempts to use Tesseract OCR functionality
- **THEN** it verifies that Tesseract is installed and accessible in system PATH
- **AND** provides clear error messages if Tesseract is missing or misconfigured
- **AND** suggests installation commands based on the operating system

#### Scenario: OCR setup documentation
- **WHEN** OCR functionality is documented for users
- **THEN** the documentation includes platform-specific installation instructions for Tesseract
- **AND** provides troubleshooting steps for common PATH configuration issues
- **AND** explains the fallback mechanism when primary OCR methods are unavailable

### Requirement: PaddleOCR API Compatibility
The system SHALL handle PaddleOCR API changes gracefully and ensure fallback OCR functionality works correctly.

#### Scenario: PaddleOCR API compatibility handling
- **WHEN** PaddleOCR is used as a fallback method for text extraction
- **THEN** the system calls PaddleOCR APIs with compatible parameter signatures
- **AND** handles deprecation warnings appropriately without breaking functionality
- **AND** provides clear logging of API compatibility adjustments made

#### Scenario: PaddleOCR parameter validation
- **WHEN** PaddleOCR methods are invoked with parameters
- **THEN** the system validates parameter names against the actual API signature
- **AND** automatically adjusts parameters that are no longer supported
- **AND** warns about parameters that are deprecated but still functional

### Requirement: OCR Fallback Strategy
The system SHALL implement a robust fallback strategy when primary OCR methods fail, ensuring text extraction attempts are made with alternative approaches.

#### Scenario: Sequential OCR fallback
- **WHEN** the primary OCR method (Tesseract) fails to extract text
- **THEN** the system automatically attempts fallback with PaddleOCR
- **AND** continues to additional fallback methods if configured
- **AND** provides comprehensive logging of each attempt and its result

#### Scenario: OCR failure recovery
- **WHEN** all OCR methods fail to extract text from an image
- **THEN** the system gracefully degrades functionality without crashing
- **AND** logs detailed failure information for debugging purposes
- **AND** continues processing other scenes or frames without interruption

### Requirement: Unified Model Storage
The system SHALL configure PaddleX models to store downloaded models in the same directory structure as Whisper and other AI models for consistent file organization.

#### Scenario: PaddleX model location configuration
- **WHEN** PaddleOCR models are downloaded or initialized
- **THEN** they are stored in the unified models directory alongside Whisper models
- **AND** follow the same naming and organizational conventions as other models
- **AND** provide configuration options to override the default storage location

#### Scenario: Model storage consistency
- **WHEN** the system manages multiple AI models
- **THEN** all models are organized in a logical directory hierarchy by model type and version
- **AND** model metadata and configuration are stored alongside the model files
- **AND** cleanup and management utilities can operate on all models uniformly

### Requirement: Verbose OCR Diagnostic Logging
The system SHALL provide verbose OCR diagnostic logging to explain low-confidence or empty OCR results, and it SHALL allow this logging to be enabled or disabled via the `OCR_VERBOSE_LOGGING_ENABLED` configuration key.

#### Scenario: Low-confidence Tesseract output
- **WHEN** Tesseract OCR returns confidence below the configured threshold
- **THEN** the system logs the confidence score, threshold, OCR language, PSM/OEM settings, and text length
- **AND** logs whether preprocessing or region-based extraction was used

#### Scenario: Empty PaddleOCR output
- **WHEN** PaddleOCR returns no text or zero lines
- **THEN** the system logs the PaddleOCR model directory, language, and detection/classification flags
- **AND** logs the number of detected boxes, collected text lines, and confidence values
- **AND** records the reason for fallback selection (e.g., empty result, lower confidence)

#### Scenario: Verbose logging toggle
- **WHEN** the `OCR_VERBOSE_LOGGING_ENABLED` flag is disabled
- **THEN** the system suppresses detailed per-engine diagnostics
- **AND** retains high-level OCR attempt and fallback summaries

#### Scenario: Verbose logging default
- **WHEN** no verbose OCR logging configuration is specified
- **THEN** verbose OCR diagnostics are enabled by default

### Requirement: OCR Quality Improvement Retries
The system SHALL attempt configurable OCR quality improvements when initial OCR confidence is low or text is empty.

#### Scenario: Preprocessing retry
- **WHEN** OCR yields empty text or confidence below threshold
- **THEN** the system retries OCR using image preprocessing (e.g., grayscale, scaling, thresholding)
- **AND** logs the preprocessing steps applied

#### Scenario: Parameter variant retry
- **WHEN** the first OCR attempt remains below the quality threshold
- **THEN** the system retries with alternative OCR parameters (e.g., PSM/OEM variants)
- **AND** selects the best result by confidence and non-empty text

#### Scenario: Retry exhaustion
- **WHEN** all retry strategies fail to improve OCR output
- **THEN** the system returns the best available result (including empty text)
- **AND** logs a structured summary of all attempted strategies and outcomes
### Requirement: Save OCR source screenshots
The system SHALL save the image(s) (full-frame or cropped region) that were used as input for OCR attempts (Tesseract, PaddleOCR, and any preprocessing variants) into the processing output directory so that extraction attempts can be inspected and evaluated.

#### Scenario: Save original source image
- **WHEN** OCR is triggered for a detected scene or frame
- **THEN** the system saves the original frame (or the cropped region passed to OCR) as an image file in the output directory alongside OCR results
- **AND** the saved image is referenced in the OCR output metadata (filename, scene id, start/end timestamps)

#### Scenario: Save preprocessing and retry variants
- **WHEN** OCR retries are performed with different preprocessing steps or parameters
- **THEN** the system saves each preprocessed image variant and records the preprocessing steps and parameters in metadata
- **AND** each saved image filename includes the OCR engine name and a stable identifier for the retry attempt (e.g., `tesseract_psm3_gray_v1.png`, `paddleocr_detect_v2.png`)

#### Scenario: Save per-engine artifacts
- **WHEN** multiple OCR engines are attempted for the same region (e.g., Tesseract then PaddleOCR)
- **THEN** the system saves separate image artifacts for each engine attempt and includes engine name, version (if known), and confidence summary in a companion JSON manifest

#### Scenario: Configurable storage and naming
- **WHEN** processing large videos or disk usage is constrained
- **THEN** saving of OCR source images can be disabled via a configuration key `OCR_SAVE_SOURCE_IMAGES_ENABLED` (default: `true`)
- **AND** the naming and directory conventions follow the existing output layout (e.g., `<output_root>/<job_id>/ocr_screenshots/<scene_id>/<timestamp>_<engine>_<variant>.png`)

#### Scenario: Accessibility for analysis
- **WHEN** processing completes
- **THEN** all saved OCR source images and their manifest files are usable for offline analysis of OCR quality and scene-level inspection

### Requirement: Video Analysis Configuration
The system SHALL provide configurable options to enable or disable video scene analysis functionality via the `VIDEO_ANALYSIS_ENABLED` setting, and video analysis SHALL be enabled by default.

#### Scenario: Configuration file control
- **WHEN** a configuration file is present
- **THEN** the system reads video analysis settings from the configuration file
- **AND** enables or disables video scene analysis based on the configuration

#### Scenario: Command-line parameter control
- **WHEN** command-line arguments are provided
- **THEN** the system accepts parameters to enable/disable video analysis
- **AND** command-line options override configuration file settings

#### Scenario: Default behavior
- **WHEN** no configuration is specified
- **THEN** video analysis is enabled by default
- **AND** users can explicitly disable video analysis functionality
