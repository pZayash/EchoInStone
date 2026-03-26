## Context

EchoInStone's `WhisperAudioTranscriber` uses HuggingFace transformers pipeline with PyTorch, supporting Intel XPU, CUDA, MPS, and CPU. The `faster-whisper` library uses CTranslate2 — a C++ inference engine that's 2-4x faster on CUDA and CPU but does not support Intel XPU.

Current transcriber at `EchoInStone/processing/whisper_audio_transcriber.py`:
- Uses `transformers.pipeline("automatic-speech-recognition", ...)`
- Has `batch_size` commented out (line 62)
- Auto-detects device: CUDA → MPS → XPU → CPU
- Returns `(text, timestamps)` tuple via `AudioTranscriberInterface`

## Goals / Non-Goals

**Goals:**
- Add faster-whisper as an alternative transcription backend for CUDA/CPU users
- Auto-select the best backend based on available hardware
- Enable batch_size in existing transformers backend for immediate speedup
- Provide a benchmark tool to compare backends empirically
- Maintain identical output format regardless of backend

**Non-Goals:**
- Replacing the transformers backend (it's the only option for Intel XPU)
- Supporting faster-whisper on Intel XPU (CTranslate2 limitation)
- Changing the `AudioTranscriberInterface` contract
- Adding new transcription models beyond Whisper variants

## Decisions

### Backend selection strategy
**Decision**: `auto` mode selects backend based on hardware availability.

Logic: if `torch.xpu.is_available()` → use transformers (only backend supporting XPU). Otherwise → use faster-whisper (faster on CUDA and CPU). Users can override with `--transcriber-backend transformers|faster-whisper`.

**Alternatives considered:**
- Always use faster-whisper with CPU fallback for XPU users: Loses XPU acceleration entirely. Unacceptable for users who chose EchoInStone specifically for Intel GPU support.
- Require explicit backend selection: Poor UX for most users who don't know their hardware details.

### FasterWhisperAudioTranscriber implementation
**Decision**: Create new class implementing `AudioTranscriberInterface`, wrapping `faster-whisper` library.

Key implementation details:
- Model: `WhisperModel("large-v3-turbo", device="cuda"|"cpu", compute_type="auto")`
- VAD filter enabled by default (skips silence, speeds up processing)
- Output conversion: faster-whisper returns `segments` iterator → convert to `(full_text, [{"timestamp": (start, end), "text": chunk_text}])` matching transformers output format
- Same progress logging pattern as existing transcriber

**Alternatives considered:**
- Subclass `WhisperAudioTranscriber`: Different library, different model loading — inheritance adds coupling without benefit.

### Batch size for transformers backend
**Decision**: Uncomment `batch_size=24` and make it configurable via `WHISPER_BATCH_SIZE` in config.

Batch processing allows the transformers pipeline to process multiple audio chunks simultaneously. This provides speedup on GPU (especially with available VRAM) with no quality impact. Default 24 matches insanely-fast-whisper's recommendation.

### Benchmark script design
**Decision**: Standalone `benchmark_transcribers.py` in project root.

Runs both backends sequentially on the same audio file, measures wall time, peak memory, and output statistics. Supports `--short` flag to process only first 60 seconds. Gracefully skips unavailable backends.

## Risks / Trade-offs

### faster-whisper dependency size
**Risk**: Adding faster-whisper increases project dependency footprint.
**Mitigation**: Add as optional Poetry extra (`poetry install --extras faster-whisper`). Not required for base installation.

### Output format differences
**Risk**: Subtle differences in timestamp boundaries between backends could affect downstream alignment.
**Mitigation**: Benchmark script compares outputs. Both backends use the same Whisper model weights — differences should be minimal.

### batch_size memory impact
**Risk**: `batch_size=24` may cause OOM on machines with limited GPU memory.
**Mitigation**: Make configurable. Document that lower values (4-8) are safer for GPUs with <8GB VRAM.

## Open Questions

1. Should the benchmark tool also measure word-level accuracy (WER) if a reference transcript is provided?
