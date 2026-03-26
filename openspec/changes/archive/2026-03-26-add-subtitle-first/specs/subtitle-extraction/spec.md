## ADDED Requirements

### Requirement: Subtitle extraction from YouTube videos
The system SHALL attempt to extract native subtitles from YouTube videos before downloading audio and running Whisper transcription. When subtitles are available and `SUBTITLE_FIRST_ENABLED` is `True`, the system SHALL use extracted subtitles instead of Whisper output.

#### Scenario: YouTube video with manual subtitles
- **WHEN** user processes a YouTube URL that has manual captions available
- **THEN** system extracts manual subtitles without downloading audio
- **AND** returns parsed subtitle text and timestamps in the internal format
- **AND** logs that subtitles were used instead of Whisper

#### Scenario: YouTube video with only auto-generated subtitles
- **WHEN** user processes a YouTube URL that has only auto-generated captions
- **AND** `SUBTITLE_PREFER_MANUAL` is `True`
- **THEN** system falls back to auto-generated subtitles
- **AND** logs a warning that auto-generated subtitles are being used

#### Scenario: YouTube video without any subtitles
- **WHEN** user processes a YouTube URL that has no subtitles available
- **THEN** system falls back to the standard pipeline: download audio → Whisper transcription
- **AND** logs that no subtitles were found

#### Scenario: Subtitle extraction disabled
- **WHEN** `SUBTITLE_FIRST_ENABLED` is `False`
- **THEN** system skips subtitle extraction entirely and proceeds with standard audio download and Whisper transcription

### Requirement: VTT/SRT subtitle parsing with deduplication
The system SHALL parse VTT and SRT subtitle formats into the internal timestamp format `[{"timestamp": (start_seconds, end_seconds), "text": str}]`. The parser SHALL deduplicate YouTube's "rolling append" auto-generated subtitles where each cue repeats the previous text.

#### Scenario: Parse standard VTT subtitle file
- **WHEN** system receives a VTT subtitle file with non-overlapping cues
- **THEN** each cue is parsed into a timestamp entry with start/end times as float seconds and text content

#### Scenario: Deduplicate rolling append subtitles
- **WHEN** system receives a VTT subtitle file with YouTube's rolling append format (each cue is a prefix of the next)
- **THEN** system removes intermediate cues and keeps only the final complete text for each segment

#### Scenario: Parse SRT subtitle file
- **WHEN** system receives an SRT subtitle file
- **THEN** each entry is parsed into the same internal timestamp format as VTT

### Requirement: Subtitle language priority
The system SHALL select subtitles based on a configurable language priority list. Manual captions SHALL be preferred over auto-generated when `SUBTITLE_PREFER_MANUAL` is `True`.

#### Scenario: Multiple languages available with priority list
- **WHEN** video has subtitles in English, Russian, and Spanish
- **AND** `SUBTITLE_PREFERRED_LANGUAGES` is `["en", "ru"]`
- **THEN** system selects English subtitles (first match in priority list)

#### Scenario: Preferred language not available
- **WHEN** video has subtitles only in Spanish
- **AND** `SUBTITLE_PREFERRED_LANGUAGES` is `["en", "ru"]`
- **THEN** system falls back to Whisper transcription
- **AND** logs that no subtitles matched preferred languages

### Requirement: Subtitle configuration
The system SHALL provide configuration options for controlling subtitle extraction behavior.

#### Scenario: Default configuration
- **WHEN** no subtitle configuration is explicitly set
- **THEN** `SUBTITLE_FIRST_ENABLED` SHALL be `True`
- **AND** `SUBTITLE_PREFERRED_LANGUAGES` SHALL be `["en", "ru"]`
- **AND** `SUBTITLE_PREFER_MANUAL` SHALL be `True`

#### Scenario: Configuration via config.py
- **WHEN** user modifies subtitle settings in `config.py`
- **THEN** the pipeline respects the updated configuration values

### Requirement: Pipeline integration with subtitle fast path
The system SHALL integrate subtitle extraction into `AudioProcessingPipeline` as an optional fast path that bypasses audio download and transcription stages.

#### Scenario: Fast path with subtitles, no diarization
- **WHEN** subtitles are successfully extracted
- **AND** diarization is not required
- **THEN** system skips audio download and Whisper transcription entirely
- **AND** returns subtitle data in the standard output format

#### Scenario: Fast path with subtitles, diarization needed
- **WHEN** subtitles are successfully extracted
- **AND** diarization is required
- **THEN** system still downloads audio for diarization
- **AND** uses extracted subtitles instead of Whisper for transcription text
- **AND** aligns subtitle timestamps with diarization output

### Requirement: Non-YouTube sources unaffected
The system SHALL not attempt subtitle extraction for non-YouTube sources (podcasts, direct audio URLs, local files). These sources SHALL continue to use the standard Whisper transcription pipeline.

#### Scenario: Podcast URL processing
- **WHEN** user processes a podcast RSS URL
- **THEN** system proceeds directly to audio download and Whisper transcription without attempting subtitle extraction

#### Scenario: Local file processing
- **WHEN** user processes a local audio file path
- **THEN** system proceeds directly to Whisper transcription without attempting subtitle extraction
