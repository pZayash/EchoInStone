## Context

EchoInStone currently follows a linear pipeline: download audio → transcribe with Whisper → diarize → align. For YouTube videos with native subtitles (manual or auto-generated), this is wasteful — subtitles can be extracted in seconds via yt-dlp metadata without downloading any media. The AI-Video-Transcriber project demonstrates this "subtitle-first" pattern effectively.

Current flow in `AudioProcessingPipeline.process()`:
1. `downloader.download(url)` → downloads full audio file
2. `transcriber.transcribe(audio_path)` → runs Whisper (5-15 min)
3. `diarizer.diarize(audio_path)` → identifies speakers
4. `aligner.align(...)` → merges transcription with diarization

The `YouTubeDownloader` already uses yt-dlp for audio download. yt-dlp also supports subtitle extraction via the same `extract_info()` call with subtitle-related options.

## Goals / Non-Goals

**Goals:**
- Extract native subtitles from YouTube before downloading audio, achieving 10-60x speedup for videos with subtitles
- Parse VTT/SRT formats into EchoInStone's internal timestamp format
- Handle YouTube's "rolling append" subtitle deduplication
- Make subtitle extraction configurable (enabled by default)
- Maintain full backward compatibility — Whisper remains the fallback

**Non-Goals:**
- Multi-platform subtitle extraction beyond yt-dlp-supported sites (future enhancement)
- Subtitle translation or language conversion
- Replacing diarization — subtitles don't identify speakers, so diarization still requires audio when needed
- Supporting subtitle editing or manual correction

## Decisions

### Subtitle extraction in YouTubeDownloader
**Decision**: Add `fetch_subtitles(url)` method to `YouTubeDownloader` rather than creating a separate subtitle extractor class.

Subtitle extraction is tightly coupled with yt-dlp and YouTube-specific behavior (rolling append dedup, language priority). Keeping it in the downloader maintains cohesion. The method uses `extract_info(url, download=False)` to query metadata without downloading content, then selectively downloads only subtitle files.

**Alternatives considered:**
- Separate `SubtitleExtractor` class: Over-engineering for a single-platform feature. Can refactor later if more platforms need custom subtitle handling.
- Adding to `DownloaderInterface`: Not all downloaders support subtitles (podcasts, direct audio files). Would pollute the interface.

### Pipeline modification approach
**Decision**: Modify `AudioProcessingPipeline.process()` to check for subtitles first when the downloader is a `YouTubeDownloader`.

The pipeline checks `isinstance(self.downloader, YouTubeDownloader)` and attempts `fetch_subtitles()` before `download()`. If subtitles are found, the pipeline converts them to the internal format and skips the transcription step. Audio is still downloaded for diarization if diarization is enabled.

**Alternatives considered:**
- New `SubtitleFirstPipeline` class: Would duplicate most of `AudioProcessingPipeline` logic. Too much code duplication for one conditional branch.
- Decorator/middleware pattern: Adds complexity without clear benefit for a single check.

### VTT/SRT parsing with deduplication
**Decision**: Implement VTT and SRT parsers within `YouTubeDownloader` with YouTube-specific deduplication.

YouTube auto-generated subtitles use a "rolling append" format where each cue repeats the previous text and appends new words. The parser detects when one cue's text is a prefix of the next cue and keeps only the final (complete) version. This logic comes from AI-Video-Transcriber's proven `_parse_vtt()` implementation.

### Subtitle-to-timestamp format conversion
**Decision**: Convert subtitles to the same `[{"timestamp": (start, end), "text": str}]` format that Whisper pipeline returns.

This ensures downstream components (aligner, data saver) work unchanged. The conversion normalizes VTT timing format (HH:MM:SS.mmm) to float seconds.

## Risks / Trade-offs

### Subtitle quality variability
**Risk**: Auto-generated YouTube subtitles may be lower quality than Whisper transcription for some content.
**Mitigation**: Configuration `SUBTITLE_PREFER_MANUAL = True` prioritizes manual captions. Users can disable subtitle-first via `SUBTITLE_FIRST_ENABLED = False` to always use Whisper.

### Diarization still requires audio download
**Risk**: When subtitles are used but diarization is also needed, audio must still be downloaded, reducing the speed benefit.
**Mitigation**: Document this trade-off. When subtitles are available, skip diarization by default (subtitles already have timing). Add `--skip-diarization` flag or auto-detect based on subtitle availability.

### yt-dlp subtitle API changes
**Risk**: yt-dlp's subtitle metadata format may change between versions.
**Mitigation**: Pin yt-dlp version, add defensive parsing with fallback to Whisper on any subtitle extraction error.

### Language mismatch
**Risk**: Extracted subtitles may be in a different language than expected.
**Mitigation**: `SUBTITLE_PREFERRED_LANGUAGES` config allows users to specify acceptable languages in priority order.

## Open Questions

1. Should auto-generated YouTube subtitles be used by default, or only manual captions? (Current decision: prefer manual, fall back to auto-generated)
2. How to handle videos with subtitles in multiple languages? (Current decision: use language priority list from config)
