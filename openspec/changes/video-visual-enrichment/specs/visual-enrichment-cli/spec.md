## ADDED Requirements

### Requirement: Job metadata on pass 1
The system SHALL write `job_metadata.json` in the job output directory when video visual
analysis runs during a normal `echoinstone` invocation (pass 1).

#### Scenario: Job metadata contents
- **WHEN** pass 1 completes with video analysis enabled
- **THEN** the system writes `<job_dir>/job_metadata.json`
- **AND** the file includes `job_id`, `echo_input`, `source_video_path` (absolute path),
  and `video_analysis_enabled`

#### Scenario: Local file source path
- **WHEN** the input is a local video file
- **THEN** `source_video_path` is the resolved absolute path to that file

#### Scenario: Downloaded video source path
- **WHEN** the input is a remote URL and the video is downloaded into the job directory
- **THEN** `source_video_path` points to the downloaded video file in the job directory

### Requirement: Two-pass CLI mode
The system SHALL support a pass-2 mode that enriches an existing job without re-running
the full audio pipeline.

#### Scenario: Pass-2 invocation
- **WHEN** the user runs `echoinstone --job-dir <path> --extract-at "mm:ss,…"`
- **THEN** the system reads `job_metadata.json` from `<path>`
- **AND** resolves the video from `source_video_path`
- **AND** does not require the positional `echo_input` argument

#### Scenario: Missing job metadata
- **WHEN** pass-2 is invoked and `job_metadata.json` is missing or lacks `source_video_path`
- **THEN** the system exits with a clear error message
- **AND** suggests re-running pass 1 with `--enable_video_analysis`

#### Scenario: Timestamp parsing
- **WHEN** `--extract-at` contains comma-separated values
- **THEN** the system accepts `mm:ss`, `hh:mm:ss`, and decimal seconds
- **AND** extracts keyframes at each parsed timestamp with trigger `phrase_timestamp`

### Requirement: Visual enrichment output contract
The system SHALL produce `visual_enrichment.json` consumable by summarization agents.

#### Scenario: Pass-2 output location
- **WHEN** pass-2 completes successfully
- **THEN** the system writes or updates `<job_dir>/visual_enrichment.json`
- **AND** writes keyframe PNGs under `<job_dir>/keyframes/`
- **AND** updates `<job_dir>/keyframes/manifest.json`

#### Scenario: Visual enrichment record shape
- **WHEN** `visual_enrichment.json` is written
- **THEN** each entry includes at minimum: `timestamp_seconds`, `trigger`, `image_path`,
  `extracted_text`, `ocr_confidence`, `ocr_engine`
- **AND** entries are ordered by `timestamp_seconds`

#### Scenario: Pass-2 merge with existing enrichment
- **WHEN** pass-2 runs on a job that already has `visual_enrichment.json` from pass 1
- **THEN** the system merges new entries without duplicating the same timestamp and trigger
- **AND** preserves existing entries

### Requirement: Agent workflow documentation
The system SHALL document the two-pass enrichment workflow for agents.

#### Scenario: CLI documentation
- **WHEN** agents read `docs/ai/echoinstone-cli.md`
- **THEN** the document describes pass 1 (transcription + optional full visual analysis)
  and pass 2 (`--job-dir` + `--extract-at`)
- **AND** lists output files agents should read (`visual_enrichment.json`, `keyframes/manifest.json`)
