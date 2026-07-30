# Spec Delta: GigaAM v3 XPU Backend

## ADDED Requirements

### Requirement: GigaAM v3 CTC transcription backend
The system SHALL provide a `GigaamAudioTranscriber` class implementing `AudioTranscriberInterface` that uses the GigaAM v3 CTC model for Russian-language transcription. The output format SHALL be identical to Whisper backends: a tuple of `(text, timestamps)` where timestamps are segment-level ASR chunks `{"timestamp": (start, end), "text"}`.

#### Scenario: Transcribe Russian audio with GigaAM on XPU
- **WHEN** GigaAM backend is selected and Intel XPU is available
- **THEN** system loads the model on XPU with fp16 encoder
- **AND** returns transcription text and segment-level timestamps in the standard format

#### Scenario: Transcribe Russian audio with GigaAM on CPU
- **WHEN** GigaAM backend is selected and no GPU/XPU is available
- **THEN** system loads the model on CPU
- **AND** returns transcription text and segment-level timestamps in the standard format

#### Scenario: GigaAM not installed
- **WHEN** `gigaam` backend is selected but the library is not installed
- **THEN** system falls back to the `transformers` backend
- **AND** logs a warning that GigaAM is not available

### Requirement: Language detection for auto backend selection
The system SHALL provide a lightweight `LanguageDetector` that identifies the dominant language of an audio file using Whisper tiny on the first ~30 seconds.

#### Scenario: Detect Russian language
- **WHEN** audio duration is greater than ~10 seconds
- **THEN** the detector runs Whisper tiny on the first ~30 seconds
- **AND** returns the detected language code

#### Scenario: Short audio skips detection
- **WHEN** audio duration is less than or equal to ~10 seconds
- **THEN** the detector returns `None`
- **AND** auto-selection falls back to the existing hardware-based logic

### Requirement: GigaAM backend configuration
The system SHALL provide configuration options for GigaAM backend selection and tuning.

#### Scenario: Default configuration
- **WHEN** no GigaAM configuration is explicitly set
- **THEN** `GIGAAM_ENABLED` SHALL be `True` when the `gigaam` extra is installed
- **AND** `GIGAAM_DEVICE` SHALL be `"auto"` (XPU if available, else CPU)
- **AND** `GIGAAM_FP16` SHALL be `True`

#### Scenario: CLI argument for GigaAM backend
- **WHEN** user provides `--transcriber-backend gigaam`
- **THEN** system uses the GigaAM backend for that run

### Requirement: GigaAM as optional Poetry extra
The system SHALL expose GigaAM as an optional dependency pinned to a specific GitHub commit, installable via `poetry install --extras gigaam`.

#### Scenario: Install GigaAM extra
- **WHEN** user runs `poetry install --extras gigaam`
- **THEN** system installs the pinned GigaAM package and its dependencies
- **AND** does not upgrade torch, pyannote-audio, or transformers

## MODIFIED Requirements

### Requirement: Backend auto-selection
The system SHALL automatically select the transcription backend based on available hardware and detected language when `TRANSCRIBER_BACKEND` is set to `"auto"`.

#### Scenario: Auto-select on Intel XPU machine
- **WHEN** `TRANSCRIBER_BACKEND` is `"auto"` and Intel XPU is available
- **THEN** system selects the `transformers` backend (WhisperAudioTranscriber)

#### Scenario: Auto-select Russian audio with GigaAM installed
- **WHEN** `TRANSCRIBER_BACKEND` is `"auto"`, GigaAM is installed, and language detection returns Russian
- **THEN** system selects the `gigaam` backend

#### Scenario: Auto-select Russian audio without GigaAM installed
- **WHEN** `TRANSCRIBER_BACKEND` is `"auto"`, GigaAM is NOT installed, and language detection returns Russian
- **THEN** system falls back to the existing hardware-based logic (XPU → transformers, else faster-whisper)

#### Scenario: Auto-select non-Russian audio
- **WHEN** `TRANSCRIBER_BACKEND` is `"auto"` and language detection returns a non-Russian language
- **THEN** system uses the existing hardware-based logic

#### Scenario: Explicit backend override
- **WHEN** user sets `--transcriber-backend gigaam` or `--transcriber-backend faster-whisper` or `--transcriber-backend transformers`
- **THEN** system uses the specified backend regardless of detected language

#### Scenario: Language detection skipped for short audio
- **WHEN** audio duration is ≤ ~10 seconds
- **THEN** language detection is skipped
- **AND** auto-selection falls back to the existing hardware-based logic
