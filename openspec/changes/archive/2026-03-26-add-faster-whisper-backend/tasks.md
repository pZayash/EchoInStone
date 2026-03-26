## 1. Dependencies and Configuration

- [x] 1.1 Add `faster-whisper` as optional Poetry dependency in `pyproject.toml` (extras group)
- [x] 1.2 Add transcriber configuration to `config.py`: `TRANSCRIBER_BACKEND`, `FASTER_WHISPER_MODEL_SIZE`, `FASTER_WHISPER_COMPUTE_TYPE`, `WHISPER_BATCH_SIZE`
- [x] 1.3 Add `--transcriber-backend` CLI argument to `main.py`

## 2. Batch Size for Existing Backend

- [x] 2.1 Uncomment and make `batch_size` configurable in `WhisperAudioTranscriber` pipeline, reading from `WHISPER_BATCH_SIZE` config
- [x] 2.2 Accept `batch_size` as constructor parameter with config default

## 3. Faster-Whisper Backend Implementation

- [x] 3.1 Create `FasterWhisperAudioTranscriber` class in `EchoInStone/processing/faster_whisper_audio_transcriber.py` implementing `AudioTranscriberInterface`
- [x] 3.2 Implement model loading with device auto-detection (CUDA/CPU) and configurable compute type
- [x] 3.3 Implement `transcribe()` method with VAD filter and progress logging
- [x] 3.4 Convert faster-whisper segment output to EchoInStone `(text, timestamps)` format
- [x] 3.5 Add graceful import handling: if `faster_whisper` not installed, raise informative error on instantiation

## 4. Backend Selection Logic

- [x] 4.1 Implement backend auto-selection logic in `main.py`: XPU → transformers, CUDA/CPU → faster-whisper
- [x] 4.2 Add fallback: if selected backend unavailable, use the other with a warning
- [x] 4.3 Wire selected transcriber into `AudioProcessingPipeline` construction

## 5. Benchmark Tool

- [x] 5.1 Create `benchmark_transcribers.py` with CLI argument parsing (audio path, `--short` flag)
- [x] 5.2 Implement audio extraction from video files (for MP4/WebM input)
- [x] 5.3 Implement `--short` mode: truncate audio to first 60 seconds using pydub
- [x] 5.4 Run both backends, measure: model load time, transcription time, peak memory
- [x] 5.5 Display comparison table with results and skip unavailable backends gracefully

## 6. Testing

- [x] 6.1 Unit tests for `FasterWhisperAudioTranscriber` output format conversion
- [x] 6.2 Unit tests for backend auto-selection logic (mock torch.xpu/cuda availability)
- [x] 6.3 Unit tests for batch_size configuration in `WhisperAudioTranscriber`
- [x] 6.4 Integration test: verify both backends produce compatible output on same audio sample
- [x] 6.5 Test graceful fallback when faster-whisper is not installed
