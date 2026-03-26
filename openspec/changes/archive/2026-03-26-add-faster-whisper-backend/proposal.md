## Why

EchoInStone uses a single Whisper transcription backend (HuggingFace transformers + PyTorch), chosen for Intel XPU support. However, on machines with NVIDIA GPUs or CPU-only setups, the `faster-whisper` library (CTranslate2-based) offers 2-4x speed improvement with lower memory usage. Adding it as an alternative backend — alongside batch_size optimization for the existing backend and a benchmark tool — lets users choose the best option for their hardware.

## What Changes

- **NEW**: Add `FasterWhisperAudioTranscriber` class implementing `AudioTranscriberInterface` using the `faster-whisper` library
- **NEW**: Add transcriber backend selection: `auto` (Intel XPU → transformers, otherwise → faster-whisper), `transformers`, `faster-whisper`
- **NEW**: Add `--transcriber-backend` CLI argument
- **ENHANCE**: Enable `batch_size=24` in existing `WhisperAudioTranscriber` pipeline (currently commented out), make it configurable via `WHISPER_BATCH_SIZE`
- **NEW**: Add `benchmark_transcribers.py` script that runs both backends on the same audio and compares speed, memory, and output quality
- **NEW**: Add `faster-whisper` as optional Poetry dependency

## Capabilities

### New Capabilities
- `transcriber-backend-selection`: Configurable selection between transformers and faster-whisper transcription backends with auto-detection based on available hardware
- `transcriber-benchmark`: CLI tool to compare transcription backends on the same audio input

### Modified Capabilities

## Impact

- **Affected code**: `WhisperAudioTranscriber` (batch_size), `config.py`, `main.py` (CLI args), new `FasterWhisperAudioTranscriber`
- **New dependencies**: `faster-whisper` (optional, via Poetry extras)
- **Architecture**: `AudioTranscriberInterface` remains unchanged — new backend is a drop-in implementation
- **Hardware**: faster-whisper supports CUDA and CPU only. Intel XPU continues to use transformers backend
- **Output format**: No change — both backends produce identical `(text, timestamps)` tuple format
