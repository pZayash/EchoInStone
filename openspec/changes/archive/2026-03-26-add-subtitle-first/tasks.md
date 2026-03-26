## 1. Configuration

- [x] 1.1 Add subtitle configuration options to `config.py`: `SUBTITLE_FIRST_ENABLED`, `SUBTITLE_PREFERRED_LANGUAGES`, `SUBTITLE_PREFER_MANUAL`
- [x] 1.2 Add `--disable-subtitle-first` CLI argument to `main.py`

## 2. Subtitle Extraction

- [x] 2.1 Add `fetch_subtitles(url) -> Optional[tuple[str, list]]` method to `YouTubeDownloader` using yt-dlp `extract_info` with subtitle options
- [x] 2.2 Implement subtitle language selection with priority (manual > auto-generated, language priority list)
- [x] 2.3 Implement VTT parser with YouTube "rolling append" deduplication
- [x] 2.4 Implement SRT parser with timestamp normalization to float seconds
- [x] 2.5 Convert parsed subtitles to internal timestamp format `[{"timestamp": (start, end), "text": str}]`

## 3. Pipeline Integration

- [x] 3.1 Modify `AudioProcessingPipeline.process()` to attempt subtitle extraction before audio download when downloader is `YouTubeDownloader`
- [x] 3.2 Implement fast path: when subtitles found and diarization not needed, skip download and transcription
- [x] 3.3 Implement hybrid path: when subtitles found but diarization needed, download audio only for diarization, use subtitles for transcription text
- [x] 3.4 Ensure fallback to standard Whisper pipeline on any subtitle extraction error

## 4. Testing

- [x] 4.1 Unit tests for VTT parser with standard and rolling-append subtitle samples
- [x] 4.2 Unit tests for SRT parser with timestamp conversion
- [x] 4.3 Unit tests for subtitle language priority selection logic
- [x] 4.4 Integration test for pipeline fast path (mock yt-dlp subtitle response)
- [x] 4.5 Integration test for fallback to Whisper when no subtitles available
- [x] 4.6 Test that non-YouTube downloaders are unaffected by subtitle-first logic
