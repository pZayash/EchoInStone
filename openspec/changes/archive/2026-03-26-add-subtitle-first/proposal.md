## Why

EchoInStone always downloads full audio and runs Whisper transcription, even for YouTube videos that already have native subtitles. This wastes 5-15 minutes per video when subtitles could be extracted in under 30 seconds. Inspired by AI-Video-Transcriber's "subtitle-first architecture", we can dramatically speed up processing for videos with existing captions while keeping Whisper as a fallback for videos without subtitles.

## What Changes

- **NEW**: Add `fetch_subtitles()` method to `YouTubeDownloader` that extracts native subtitles via yt-dlp metadata before downloading audio
- **NEW**: Implement VTT/SRT subtitle parsing with deduplication of YouTube's "rolling append" format
- **NEW**: Add subtitle language priority configuration (manual captions preferred over auto-generated)
- **CHANGE**: Modify `AudioProcessingPipeline.process()` to attempt subtitle extraction first, skipping audio download and Whisper transcription when subtitles are available
- **NEW**: Add configuration options: `SUBTITLE_FIRST_ENABLED`, `SUBTITLE_PREFERRED_LANGUAGES`, `SUBTITLE_PREFER_MANUAL`
- **CHANGE**: Convert subtitle timestamps to EchoInStone's internal timestamp format for compatibility with the alignment pipeline

## Capabilities

### New Capabilities
- `subtitle-extraction`: Extract and parse native subtitles from YouTube (and other yt-dlp-supported platforms) as a fast alternative to Whisper transcription

### Modified Capabilities

## Impact

- **Affected code**: `YouTubeDownloader`, `AudioProcessingPipeline`, `config.py`, `main.py` (CLI args)
- **Affected architecture**: Processing pipeline gains a "fast path" that bypasses download + transcribe stages
- **Dependencies**: No new dependencies (yt-dlp already supports subtitle extraction)
- **Diarization**: When subtitles are used, diarization still requires audio download (handled as optional step)
- **Output format**: No change to output format - subtitles are converted to the same timestamp structure as Whisper output
