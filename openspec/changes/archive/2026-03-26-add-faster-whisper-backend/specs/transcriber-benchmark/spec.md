## ADDED Requirements

### Requirement: Transcriber benchmark tool
The system SHALL provide a `benchmark_transcribers.py` CLI script that compares transcription backends on the same audio input, measuring performance and output quality.

#### Scenario: Benchmark both backends on full audio
- **WHEN** user runs `python benchmark_transcribers.py <audio_file>`
- **THEN** system runs both `transformers` and `faster-whisper` backends on the same audio
- **AND** displays a comparison table with: model load time, transcription time, peak memory usage, output text length, number of timestamp chunks

#### Scenario: Benchmark with short mode
- **WHEN** user runs `python benchmark_transcribers.py <audio_file> --short`
- **THEN** system extracts only the first 60 seconds of audio
- **AND** runs both backends on the truncated audio
- **AND** displays the same comparison table

#### Scenario: Backend not available
- **WHEN** one of the backends is not available (e.g., no XPU for transformers, or faster-whisper not installed)
- **THEN** system skips that backend with an informational message
- **AND** runs and reports results only for the available backend

#### Scenario: Video file input
- **WHEN** user provides a video file (MP4, WebM) instead of audio
- **THEN** system extracts audio from the video file before benchmarking
