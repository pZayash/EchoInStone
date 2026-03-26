import pytest
from unittest.mock import patch, MagicMock
from EchoInStone.capture.youtube_downloader import YouTubeDownloader
from EchoInStone.processing.audio_processing_pipeline import AudioProcessingPipeline
from EchoInStone.capture.audio_downloader import AudioDownloader


# --- VTT Samples ---

SAMPLE_VTT_STANDARD = """\
WEBVTT

00:00:01.000 --> 00:00:04.000
Hello, welcome to the video.

00:00:04.500 --> 00:00:08.000
Today we will discuss testing.

00:00:08.500 --> 00:00:12.000
Let's get started.
"""

SAMPLE_VTT_ROLLING_APPEND = """\
WEBVTT

00:00:01.000 --> 00:00:03.000
Hello

00:00:03.000 --> 00:00:05.000
Hello welcome

00:00:05.000 --> 00:00:07.000
Hello welcome to the video

00:00:08.000 --> 00:00:10.000
Today we

00:00:10.000 --> 00:00:12.000
Today we discuss testing
"""

SAMPLE_VTT_WITH_TAGS = """\
WEBVTT

00:00:01.000 --> 00:00:04.000
<c>Hello</c> <c>world</c>

00:00:05.000 --> 00:00:08.000
<b>Bold text</b> and <i>italic</i>
"""

# --- SRT Samples ---

SAMPLE_SRT = """\
1
00:00:01,000 --> 00:00:04,000
Hello, welcome to the video.

2
00:00:04,500 --> 00:00:08,000
Today we will discuss testing.

3
00:00:08,500 --> 00:00:12,000
Let's get started.
"""

SAMPLE_SRT_WITH_TAGS = """\
1
00:01:30,500 --> 00:01:35,200
<font color="#ffffff">Subtitle with HTML tags</font>
"""


class TestVTTParser:
    """4.1 Unit tests for VTT parser with standard and rolling-append subtitle samples."""

    def test_parse_standard_vtt(self):
        entries = YouTubeDownloader._parse_vtt(SAMPLE_VTT_STANDARD)
        assert len(entries) == 3
        assert entries[0]["text"] == "Hello, welcome to the video."
        assert entries[0]["timestamp"] == (1.0, 4.0)
        assert entries[1]["text"] == "Today we will discuss testing."
        assert entries[1]["timestamp"] == (4.5, 8.0)
        assert entries[2]["text"] == "Let's get started."
        assert entries[2]["timestamp"] == (8.5, 12.0)

    def test_parse_rolling_append_vtt_deduplication(self):
        entries = YouTubeDownloader._parse_vtt(SAMPLE_VTT_ROLLING_APPEND)
        # After dedup: "Hello welcome to the video" and "Today we discuss testing"
        assert len(entries) == 2
        assert entries[0]["text"] == "Hello welcome to the video"
        assert entries[0]["timestamp"] == (5.0, 7.0)
        assert entries[1]["text"] == "Today we discuss testing"
        assert entries[1]["timestamp"] == (10.0, 12.0)

    def test_parse_vtt_strips_html_tags(self):
        entries = YouTubeDownloader._parse_vtt(SAMPLE_VTT_WITH_TAGS)
        assert len(entries) == 2
        assert entries[0]["text"] == "Hello world"
        assert entries[1]["text"] == "Bold text and italic"

    def test_parse_empty_vtt(self):
        entries = YouTubeDownloader._parse_vtt("WEBVTT\n\n")
        assert entries == []

    def test_timestamp_conversion_hours(self):
        vtt = "WEBVTT\n\n01:30:15.500 --> 01:30:20.250\nText at 1h30m."
        entries = YouTubeDownloader._parse_vtt(vtt)
        assert len(entries) == 1
        assert entries[0]["timestamp"][0] == pytest.approx(5415.5)
        assert entries[0]["timestamp"][1] == pytest.approx(5420.25)


class TestSRTParser:
    """4.2 Unit tests for SRT parser with timestamp conversion."""

    def test_parse_standard_srt(self):
        entries = YouTubeDownloader._parse_srt(SAMPLE_SRT)
        assert len(entries) == 3
        assert entries[0]["text"] == "Hello, welcome to the video."
        assert entries[0]["timestamp"] == (1.0, 4.0)
        assert entries[1]["timestamp"] == (4.5, 8.0)
        assert entries[2]["timestamp"] == (8.5, 12.0)

    def test_parse_srt_strips_html_tags(self):
        entries = YouTubeDownloader._parse_srt(SAMPLE_SRT_WITH_TAGS)
        assert len(entries) == 1
        assert entries[0]["text"] == "Subtitle with HTML tags"
        assert entries[0]["timestamp"] == (90.5, 95.2)

    def test_parse_empty_srt(self):
        entries = YouTubeDownloader._parse_srt("")
        assert entries == []

    def test_srt_timestamp_normalization(self):
        srt = "1\n00:02:03,456 --> 00:02:05,789\nSome text\n"
        entries = YouTubeDownloader._parse_srt(srt)
        assert len(entries) == 1
        assert entries[0]["timestamp"][0] == pytest.approx(123.456)
        assert entries[0]["timestamp"][1] == pytest.approx(125.789)


class TestSubtitleLanguageSelection:
    """4.3 Unit tests for subtitle language priority selection logic."""

    def setup_method(self):
        self.downloader = YouTubeDownloader(output_dir="/tmp/test")

    @patch("EchoInStone.capture.youtube_downloader.SUBTITLE_PREFERRED_LANGUAGES", ["en", "ru"])
    @patch("EchoInStone.capture.youtube_downloader.SUBTITLE_PREFER_MANUAL", True)
    def test_prefers_manual_over_auto(self):
        manual = {"en": [{"ext": "vtt", "url": "http://manual"}]}
        auto = {"en": [{"ext": "vtt", "url": "http://auto"}]}
        result = self.downloader._select_subtitles(manual, auto)
        assert result is not None
        lang, sub_info, is_auto = result
        assert lang == "en"
        assert is_auto is False

    @patch("EchoInStone.capture.youtube_downloader.SUBTITLE_PREFERRED_LANGUAGES", ["en", "ru"])
    @patch("EchoInStone.capture.youtube_downloader.SUBTITLE_PREFER_MANUAL", True)
    def test_falls_back_to_auto_when_no_manual(self):
        manual = {}
        auto = {"en": [{"ext": "vtt", "url": "http://auto"}]}
        result = self.downloader._select_subtitles(manual, auto)
        assert result is not None
        lang, _, is_auto = result
        assert lang == "en"
        assert is_auto is True

    @patch("EchoInStone.capture.youtube_downloader.SUBTITLE_PREFERRED_LANGUAGES", ["en", "ru"])
    @patch("EchoInStone.capture.youtube_downloader.SUBTITLE_PREFER_MANUAL", True)
    def test_language_priority_order(self):
        manual = {"ru": [{"ext": "vtt", "url": "http://ru"}]}
        auto = {"es": [{"ext": "vtt", "url": "http://es"}]}
        result = self.downloader._select_subtitles(manual, auto)
        assert result is not None
        lang, _, _ = result
        assert lang == "ru"

    @patch("EchoInStone.capture.youtube_downloader.SUBTITLE_PREFERRED_LANGUAGES", ["en", "ru"])
    @patch("EchoInStone.capture.youtube_downloader.SUBTITLE_PREFER_MANUAL", True)
    def test_no_match_returns_none(self):
        manual = {"fr": [{"ext": "vtt", "url": "http://fr"}]}
        auto = {"es": [{"ext": "vtt", "url": "http://es"}]}
        result = self.downloader._select_subtitles(manual, auto)
        assert result is None

    @patch("EchoInStone.capture.youtube_downloader.SUBTITLE_PREFERRED_LANGUAGES", ["en"])
    @patch("EchoInStone.capture.youtube_downloader.SUBTITLE_PREFER_MANUAL", False)
    def test_auto_preferred_when_manual_pref_disabled(self):
        manual = {"en": [{"ext": "vtt", "url": "http://manual"}]}
        auto = {"en": [{"ext": "vtt", "url": "http://auto"}]}
        result = self.downloader._select_subtitles(manual, auto)
        assert result is not None
        _, _, is_auto = result
        assert is_auto is True


class TestPipelineFastPath:
    """4.4 Integration test for pipeline fast path (mock yt-dlp subtitle response)."""

    def setup_method(self):
        self.downloader = MagicMock(spec=YouTubeDownloader)
        self.transcriber = MagicMock()
        self.diarizer = MagicMock()
        self.aligner = MagicMock()
        self.saver = MagicMock()

    def test_fast_path_skips_download_and_transcription(self):
        subtitle_entries = [
            {"timestamp": (1.0, 4.0), "text": "Hello"},
            {"timestamp": (5.0, 8.0), "text": "World"},
        ]
        self.downloader.fetch_subtitles.return_value = ("en", subtitle_entries)

        pipeline = AudioProcessingPipeline(
            self.downloader, self.transcriber, self.diarizer,
            self.aligner, self.saver, subtitle_first=True
        )
        result = pipeline.process("https://youtube.com/watch?v=test")

        assert result is not None
        assert len(result) == 2
        assert result[0] == ("", 1.0, 4.0, "Hello")
        assert result[1] == ("", 5.0, 8.0, "World")

        # Verify download and transcription were NOT called
        self.downloader.download.assert_not_called()
        self.transcriber.transcribe.assert_not_called()
        self.diarizer.diarize.assert_not_called()


class TestPipelineFallback:
    """4.5 Integration test for fallback to Whisper when no subtitles available."""

    def test_fallback_when_no_subtitles(self):
        downloader = MagicMock(spec=YouTubeDownloader)
        transcriber = MagicMock()
        diarizer = MagicMock()
        aligner = MagicMock()
        saver = MagicMock()

        downloader.fetch_subtitles.return_value = None
        downloader.download.return_value = "/tmp/audio.wav"
        transcriber.transcribe.return_value = ("text", [{"timestamp": (0, 1)}])
        diarizer.diarize.return_value = "diarization"
        aligner.align.return_value = [("SPEAKER_00", 0, 1, "text")]

        pipeline = AudioProcessingPipeline(
            downloader, transcriber, diarizer,
            aligner, saver, subtitle_first=True
        )
        result = pipeline.process("https://youtube.com/watch?v=test")

        downloader.download.assert_called_once()
        transcriber.transcribe.assert_called_once()
        assert result == [("SPEAKER_00", 0, 1, "text")]

    def test_fallback_on_subtitle_extraction_error(self):
        downloader = MagicMock(spec=YouTubeDownloader)
        transcriber = MagicMock()
        diarizer = MagicMock()
        aligner = MagicMock()
        saver = MagicMock()

        downloader.fetch_subtitles.side_effect = Exception("yt-dlp error")
        downloader.download.return_value = "/tmp/audio.wav"
        transcriber.transcribe.return_value = ("text", [])
        diarizer.diarize.return_value = "diarization"
        aligner.align.return_value = [("SPEAKER_00", 0, 1, "text")]

        pipeline = AudioProcessingPipeline(
            downloader, transcriber, diarizer,
            aligner, saver, subtitle_first=True
        )
        result = pipeline.process("https://youtube.com/watch?v=test")

        downloader.download.assert_called_once()
        assert result is not None


class TestNonYouTubeUnaffected:
    """4.6 Test that non-YouTube downloaders are unaffected by subtitle-first logic."""

    def test_non_youtube_downloader_skips_subtitle_path(self):
        downloader = MagicMock(spec=AudioDownloader)
        transcriber = MagicMock()
        diarizer = MagicMock()
        aligner = MagicMock()
        saver = MagicMock()

        downloader.download.return_value = "/tmp/audio.wav"
        transcriber.transcribe.return_value = ("text", [])
        diarizer.diarize.return_value = "diarization"
        aligner.align.return_value = [("SPEAKER_00", 0, 1, "text")]

        pipeline = AudioProcessingPipeline(
            downloader, transcriber, diarizer,
            aligner, saver, subtitle_first=True
        )
        result = pipeline.process("https://example.com/audio.mp3")

        # Should go directly to download, no fetch_subtitles
        assert not hasattr(downloader, 'fetch_subtitles') or not downloader.fetch_subtitles.called
        downloader.download.assert_called_once()
        assert result is not None
