## ADDED Requirements

### Requirement: Trigger-based keyframe extraction
The system SHALL extract **Keyframes** from video files when configured **Triggers** fire:
`scene_boundary` (hash/SSIM visual change), `periodic_fallback` (timer), and
`phrase_timestamp` (explicit timestamps from CLI).

#### Scenario: Scene boundary trigger
- **WHEN** a video is processed with visual analysis enabled
- **THEN** the system detects visual changes using a hash or SSIM-based boundary detector
- **AND** extracts a keyframe at each detected boundary timestamp
- **AND** records trigger type `scene_boundary` in the keyframe manifest

#### Scenario: Periodic fallback trigger
- **WHEN** visual analysis is enabled and `KEYFRAME_PERIODIC_INTERVAL_SECONDS` is configured
- **THEN** the system extracts a keyframe at each periodic interval throughout the video duration
- **AND** records trigger type `periodic_fallback` in the keyframe manifest
- **AND** deduplicates keyframes that fall within 0.5 seconds of an existing trigger

#### Scenario: Phrase timestamp trigger
- **WHEN** pass-2 CLI provides `--extract-at` timestamps
- **THEN** the system extracts a keyframe at each specified timestamp
- **AND** records trigger type `phrase_timestamp` in the keyframe manifest

### Requirement: Keyframe artifact storage
The system SHALL persist each keyframe as a first-class PNG artifact with a companion manifest.

#### Scenario: Keyframe PNG naming and location
- **WHEN** a keyframe is extracted
- **THEN** the system saves a PNG under `<job_dir>/keyframes/`
- **AND** names the file `{seconds_ms}_{trigger}_{short_id}.png`
- **AND** adds an entry to `<job_dir>/keyframes/manifest.json`

#### Scenario: Keyframe manifest entry
- **WHEN** a keyframe is saved
- **THEN** the manifest entry includes `id`, `timestamp_seconds`, `trigger`, `image_path`,
  `ocr_text`, `ocr_confidence`, `ocr_engine`, and `created_at`
- **AND** the manifest is valid JSON and append-safe for pass-2 runs

### Requirement: Keyframe deduplication and limits
The system SHALL prevent unbounded keyframe growth on long videos.

#### Scenario: Timestamp deduplication
- **WHEN** multiple triggers fire within 0.5 seconds of each other
- **THEN** the system keeps a single keyframe at the earliest timestamp
- **AND** records all contributing trigger types in metadata when applicable

#### Scenario: Maximum keyframes per job
- **WHEN** the number of triggers exceeds `KEYFRAME_MAX_PER_JOB`
- **THEN** the system logs a warning
- **AND** prioritizes `phrase_timestamp` and `scene_boundary` triggers over `periodic_fallback`
- **AND** continues processing without crashing

### Requirement: Keyframe at boundary not mid-scene
The system SHALL extract OCR input frames at trigger timestamps, not at arbitrary mid-scene sample points.

#### Scenario: Boundary-aligned capture
- **WHEN** a `scene_boundary` trigger fires at time T
- **THEN** the captured frame represents the visual content at or immediately after time T
- **AND** the system does not use only mid-scene sampling as the sole capture strategy
