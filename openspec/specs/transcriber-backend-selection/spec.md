## ADDED Requirements

### Requirement: Faster-Whisper transcription backend
The system SHALL provide a `FasterWhisperAudioTranscriber` class implementing `AudioTranscriberInterface` that uses the `faster-whisper` library for transcription. The output format SHALL be identical to `WhisperAudioTranscriber`: a tuple of `(text, timestamps)`.

#### Scenario: Transcribe audio with faster-whisper on CUDA
- **WHEN** faster-whisper backend is selected and CUDA is available
- **THEN** system loads the model on CUDA with float16 compute type
- **AND** returns transcription text and timestamps in the standard format

#### Scenario: Transcribe audio with faster-whisper on CPU
- **WHEN** faster-whisper backend is selected and no GPU is available
- **THEN** system loads the model on CPU with int8 compute type
- **AND** returns transcription text and timestamps in the standard format

#### Scenario: VAD filter enabled by default
- **WHEN** faster-whisper transcribes audio containing silent segments
- **THEN** system skips silent segments via VAD filter
- **AND** transcription timestamps reflect only speech segments

### Requirement: Backend auto-selection
The system SHALL automatically select the transcription backend based on available hardware when `TRANSCRIBER_BACKEND` is set to `"auto"`.

#### Scenario: Auto-select on Intel XPU machine
- **WHEN** `TRANSCRIBER_BACKEND` is `"auto"` and Intel XPU is available
- **THEN** system selects the `transformers` backend (WhisperAudioTranscriber)

#### Scenario: Auto-select on NVIDIA GPU machine
- **WHEN** `TRANSCRIBER_BACKEND` is `"auto"` and CUDA is available but XPU is not
- **THEN** system selects the `faster-whisper` backend (FasterWhisperAudioTranscriber)

#### Scenario: Auto-select on CPU-only machine
- **WHEN** `TRANSCRIBER_BACKEND` is `"auto"` and neither XPU nor CUDA is available
- **THEN** system selects the `faster-whisper` backend with CPU compute

#### Scenario: Explicit backend override
- **WHEN** user sets `--transcriber-backend faster-whisper` or `--transcriber-backend transformers`
- **THEN** system uses the specified backend regardless of available hardware

#### Scenario: Faster-whisper not installed
- **WHEN** `faster-whisper` backend is selected but the library is not installed
- **THEN** system falls back to `transformers` backend
- **AND** logs a warning that faster-whisper is not available

### Requirement: Backend configuration
The system SHALL provide configuration options for transcription backend selection and tuning.

#### Scenario: Default configuration
- **WHEN** no transcriber configuration is explicitly set
- **THEN** `TRANSCRIBER_BACKEND` SHALL be `"auto"`
- **AND** `FASTER_WHISPER_MODEL_SIZE` SHALL be `"large-v3-turbo"`
- **AND** `FASTER_WHISPER_COMPUTE_TYPE` SHALL be `"auto"`
- **AND** `WHISPER_BATCH_SIZE` SHALL be `24`

#### Scenario: CLI argument for backend selection
- **WHEN** user provides `--transcriber-backend` argument
- **THEN** system uses the specified backend for that run

### Requirement: Batch size for transformers backend
The system SHALL support configurable batch processing in the existing `WhisperAudioTranscriber` via `WHISPER_BATCH_SIZE` configuration.

#### Scenario: Batch processing enabled
- **WHEN** `WHISPER_BATCH_SIZE` is set to a positive integer
- **THEN** `WhisperAudioTranscriber` processes audio chunks in batches of that size

#### Scenario: Batch processing disabled
- **WHEN** `WHISPER_BATCH_SIZE` is set to `1` or `None`
- **THEN** `WhisperAudioTranscriber` processes audio chunks sequentially
