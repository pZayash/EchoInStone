# Tasks: Add GigaAM v3 XPU Backend

## 1. Preparation
- [x] 1.1 Verify Poetry environment is clean and `torch 2.7.0+xpu` is active.
- [x] 1.2 Create `results_test/` fixture: short Russian audio clip (e.g., 15–60 s from `input.mp3` or a known sample) with reference transcript for quality comparison.

## 2. Add GigaAM dependency
- [x] 2.1 Add `gigaam` optional dependency to `pyproject.toml` pinned to GitHub commit `6e4b027c6fb554e09e8b9059b757a175295ab879`.
- [x] 2.2 Add `gigaam` extra to `[tool.poetry.extras]`.
- [x] 2.3 Run `poetry lock` and `poetry install --extras gigaam`; verify no conflicts with torch/pyannote/transformers.

## 3. Implement LanguageDetector
- [x] 3.1 Create `EchoInStone/processing/language_detector.py` with class `LanguageDetector`.
- [x] 3.2 Use Whisper tiny via HuggingFace Transformers on first ~30 s of audio.
- [x] 3.3 Skip detection for audio ≤ ~10 s; return `None`.
- [x] 3.4 Unit test: mock audio and verify detection returns expected language.

## 4. Implement GigaamAudioTranscriber
- [x] 4.1 Create `EchoInStone/processing/gigaam_audio_transcriber.py` implementing `AudioTranscriberInterface`.
- [x] 4.2 Load GigaAM v3 CTC with `device="auto"` (XPU if available, else CPU), `fp16_encoder=True`.
- [x] 4.3 Implement chunking: split audio into ~25 s segments with ~20 s shift (or use PyDub slicing); run `model.transcribe()` per chunk.
- [x] 4.4 Map word-level output to segment-level ASR chunks `{"timestamp": (start, end), "text"}`; merge words by pause threshold.
- [x] 4.5 Return `(full_text, timestamps)` matching Whisper backend format.
- [x] 4.6 Unit test: mock GigaAM, verify output format and chunk merging.

## 5. Integrate into create_transcriber
- [x] 5.1 Update `main.py` `create_transcriber()` to accept `"gigaam"` backend.
- [x] 5.2 Extend `auto` logic: if `auto` and GigaAM installed and `LanguageDetector` returns Russian → select GigaAM.
- [x] 5.3 Add CLI argument validation for `gigaam` value.

## 6. Configuration
- [x] 6.1 Add to `EchoInStone/config.py`: `GIGAAM_ENABLED`, `GIGAAM_DEVICE`, `GIGAAM_FP16`, `GIGAAM_CHUNK_LENGTH`, `GIGAAM_CHUNK_SHIFT`, `GIGAAM_PAUSE_THRESHOLD`.
- [x] 6.2 Mirror in `config_private.py` if needed (structure only, no secrets).

## 7. Testing
- [x] 7.1 Unit tests for `LanguageDetector` and `GigaamAudioTranscriber` in `tests/`.
- [x] 7.2 Update `tests/test_transcriber_backends.py` to cover `gigaam` backend and auto-selection.
- [x] 7.3 Run `poetry run pytest` — all existing tests pass.
- [ ] 7.4 BDD scenario in `features/` for Russian transcription with GigaAM (optional if coverage is sufficient).

## 8. Benchmark and validation
- [x] 8.1 Run `results_test/` benchmark: GigaAM vs Whisper (transformers) on the Russian fixture.
- [x] 8.2 Compare transcript quality (manual or WER proxy) and wall time.
- [x] 8.3 Write `results_test/gigaam_benchmark_report.md` with findings.
- [x] 8.4 Verify no regression on English audio (Whisper path unchanged).

## 9. Documentation
- [x] 9.1 Update `README.md` with GigaAM installation and usage instructions.
- [x] 9.2 Update `docs/ai/echoinstone-cli.md` with `--transcriber-backend gigaam` option.
- [x] 9.3 Note the `PYTHONIOENCODING=utf-8` recommendation for Windows console.

## 10. Cleanup
- [x] 10.1 Remove or archive `results_test/gigaam_xpu_spike/` venv (keep `REPORT.md`).
- [x] 10.2 Archive change via `openspec archive`.
