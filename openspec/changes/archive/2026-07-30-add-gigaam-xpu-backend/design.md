# Design: GigaAM v3 XPU Backend

## Context

EchoInStone currently supports two Whisper backends: HuggingFace Transformers (optimized for Intel XPU) and faster-whisper (CTranslate2, CUDA/CPU). Russian-language transcription is a major use case, and Whisper Large v3 Turbo is slower and less accurate for Russian than GigaAM v3 CTC. A spike on the operator's Intel Arc 140T (XPU) confirmed GigaAM v3 CTC works natively on XPU, produces correct Russian transcripts, and achieves ~40x realtime warm on 15 s clips. The GigaAM package is available only from a GitHub commit (PyPI lacks v3), and its `[longform]` extra conflicts with the project's torch/pyannote/transformers versions.

## Goals / Non-Goals

**Goals:**
- Add GigaAM v3 CTC as an optional backend with identical `AudioTranscriberInterface` contract.
- Auto-select GigaAM when the detected language is Russian and the user hasn't explicitly chosen a backend.
- Preserve existing diarization and alignment by converting GigaAM output to standard ASR chunks.
- Keep the Poetry environment clean: GigaAM as an optional extra, no forced upgrades.

**Non-Goals:**
- KenLM / CTC+LM decoding (follow-up change).
- Porting zapis's `LongformCTC` algorithm (we use our own chunking).
- OpenVINO / NPU GigaAM variants.
- Changing default behavior for non-Russian audio.
- Modifying existing Whisper backends or diarization.

## Decisions

### 1. GigaAM as optional Poetry extra
- **Decision:** Add `gigaam` as an optional dependency pinned to a specific GitHub commit (`6e4b027c6fb554e09e8b9059b757a175295ab879`), without its `[longform]` extra.
- **Rationale:** The `[longform]` extra pins `torch==2.10.*`, `pyannote.audio==4.0.*`, `transformers==5.*`, which conflict with the project's `torch 2.7.0+xpu`, `pyannote-audio ^3.3.2`, `transformers ^4.50`.
- **Alternative:** Vendored copy of zapis's `gigaam_engine.py` — rejected: duplicates upstream logic, harder to update.

### 2. Adapter converts GigaAM words to ASR chunks
- **Decision:** `GigaamAudioTranscriber` runs GigaAM on audio chunks (via PyDub/ffmpeg slicing or native `transcribe()` per ~25 s window) and maps word-level timestamps into EchoInStone's segment-level `{"timestamp": (start, end), "text"}` chunks.
- **Rationale:** Keeps `SpeakerAligner` and diarization untouched; avoids breaking the contract.
- **Alternative:** Pass word-level timestamps directly — rejected: aligner expects segment-level chunks.

### 3. Language detection via Whisper tiny
- **Decision:** A lightweight `LanguageDetector` runs Whisper tiny (Transformers, XPU) on the first ~30 s of audio when duration > ~10 s.
- **Rationale:** Reuses existing torch/XPU infrastructure; avoids extra dependencies like langdetect/langid.
- **Alternative:** Detect from subtitle language or filename — rejected: unreliable.

### 4. Auto-select GigaAM only for Russian
- **Decision:** Extend `create_transcriber("auto")` to detect Russian and route to GigaAM if available; otherwise fall back to the existing XPU/CUDA/CPU Whisper logic.
- **Rationale:** Matches operator intent; non-Russian audio unchanged.
- **Alternative:** Always prefer GigaAM on XPU — rejected: GigaAM is Russian-only.

### 5. Greedy decoding only
- **Decision:** Use GigaAM's default greedy decoding; do not integrate KenLM in this change.
- **Rationale:** KenLM on Windows requires MSVC or prebuilt wheels; spike didn't verify it. Greedy is sufficient for quality improvement over Whisper.
- **Alternative:** Bundle KenLM wheels — rejected: adds complexity, unverified on XPU.

## Risks / Trade-offs

- **STFT XPU→CPU fallback** → Mel-spectrogram STFT falls back to CPU, one memcpy per call. Mitigation: acceptable for short/medium audio; benchmark before making XPU the default device.
- **GigaAM package availability** → Pinned GitHub commit may become unavailable. Mitigation: document SHA, consider vendoring if upstream is unstable.
- **Word→chunk merge quality** → Pause-threshold merging may split sentences differently than Whisper. Mitigation: benchmark against Whisper on a Russian fixture; tune `pause_threshold` if needed.
- **Windows encoding** → Console may mojibake Russian text. Mitigation: set `PYTHONIOENCODING=utf-8` in launcher scripts or document.

## Migration Plan

1. Add `gigaam` extra to `pyproject.toml` with pinned commit.
2. Implement `GigaamAudioTranscriber` and `LanguageDetector`.
3. Extend `create_transcriber` and config.
4. Run benchmark: GigaAM vs Whisper on Russian fixture; validate transcript quality and speed.
5. Document installation: `poetry install --extras gigaam`.

## Open Questions

- Exact chunk length and overlap for GigaAM longform (start with ~25 s / ~20 s shift, tune based on benchmark).
- Whether to expose `GIGAAM_DEVICE` config override (default: auto → XPU if available, else CPU).
