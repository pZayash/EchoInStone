# Proposal: Add GigaAM v3 XPU Backend

## Why

EchoInStone's ASR stack is Whisper-only. For Russian audio — a major use case — Whisper Large v3 Turbo is accurate but slower and less optimized than GigaAM v3 CTC. A spike on the operator's Intel Arc 140T (XPU) confirmed GigaAM v3 CTC runs natively on XPU (`device="xpu"`), produces correct Russian transcripts, and achieves ~40x realtime warm on 15 s clips. Adding GigaAM as an optional backend improves Russian transcription speed and quality without disrupting existing Whisper paths.

## What Changes

- Add optional **GigaAM v3 CTC** backend implementing `AudioTranscriberInterface`, exposed as `--transcriber-backend gigaam` and config `TRANSCRIBER_BACKEND = "gigaam"`.
- Auto-select GigaAM when `TRANSCRIBER_BACKEND = "auto"` and a lightweight language detector identifies Russian (Whisper tiny on first ~30 s of audio > ~10 s duration).
- Adapter converts GigaAM word-level output into EchoInStone's standard ASR chunks (segment-level `{"timestamp": (start, end), "text"}`) so alignment and diarization remain unchanged.
- Poetry extra `gigaam` pins the backend to a specific GigaAM commit (avoiding the `[longform]` extra, which conflicts with the project's torch/pyannote/transformers versions).
- Greedy decoding only in this change; KenLM/CTC+LM is a follow-up.

## Capabilities

### New Capabilities
- `gigaam-transcription`: GigaAM v3 CTC backend, language detection, adapter, config, CLI flag.

### Modified Capabilities
- `transcriber-backend-selection`: Extend auto-selection to consider detected Russian language and route to GigaAM when appropriate.

## Impact

- `EchoInStone/processing/gigaam_audio_transcriber.py` (new)
- `EchoInStone/processing/language_detector.py` (new, lightweight)
- `EchoInStone/config.py` — add GigaAM settings
- `main.py` — extend `create_transcriber`
- `pyproject.toml` — add optional `gigaam` dependency and extra
- `results_test/` — benchmark fixture and report comparing GigaAM vs Whisper on Russian audio
- No changes to diarization, alignment, or existing Whisper backends
