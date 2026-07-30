# Spec Delta: Transcriber Backend Selection (MODIFIED)

## MODIFIED Requirements

### Requirement: Backend auto-selection
The system SHALL automatically select the transcription backend based on available hardware and detected language when `TRANSCRIBER_BACKEND` is set to `"auto"`.

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
- **WHEN** user sets `--transcriber-backend faster-whisper` or `--transcriber-backend transformers` or `--transcriber-backend gigaam`
- **THEN** system uses the specified backend regardless of available hardware or detected language

#### Scenario: Faster-whisper not installed
- **WHEN** `faster-whisper` backend is selected but the library is not installed
- **THEN** system falls back to `transformers` backend
- **AND** logs a warning that faster-whisper is not available

#### Scenario: GigaAM not installed
- **WHEN** `gigaam` backend is selected but the library is not installed
- **THEN** system falls back to `transformers` backend
- **AND** logs a warning that GigaAM is not available

#### Scenario: Auto-select Russian audio with GigaAM installed
- **WHEN** `TRANSCRIBER_BACKEND` is `"auto"`, GigaAM is installed, and language detection returns Russian
- **THEN** system selects the `gigaam` backend

#### Scenario: Auto-select Russian audio without GigaAM installed
- **WHEN** `TRANSCRIBER_BACKEND` is `"auto"`, GigaAM is NOT installed, and language detection returns Russian
- **THEN** system falls back to the existing hardware-based logic

#### Scenario: Auto-select non-Russian audio
- **WHEN** `TRANSCRIBER_BACKEND` is `"auto"` and language detection returns a non-Russian language
- **THEN** system uses the existing hardware-based logic

#### Scenario: Language detection skipped for short audio
- **WHEN** audio duration is ≤ ~10 seconds
- **THEN** language detection is skipped
- **AND** auto-selection falls back to the existing hardware-based logic
