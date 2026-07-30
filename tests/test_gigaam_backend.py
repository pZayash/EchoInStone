"""Unit tests for GigaAM backend and language detection."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from EchoInStone.processing.language_detector import LanguageDetector
from EchoInStone.processing.gigaam_audio_transcriber import GigaamAudioTranscriber


def _make_wav(tmp_path, duration_ms=1000, filename="test.wav"):
    """Create a silent WAV file using pydub."""
    from pydub import AudioSegment
    audio = AudioSegment.silent(duration=duration_ms)
    path = tmp_path / filename
    audio.export(str(path), format="wav")
    return str(path)


class TestLanguageDetector:
    """Tests for LanguageDetector."""

    def test_detect_short_audio_returns_none(self, tmp_path):
        """Audio ≤10s should skip detection."""
        short_audio = _make_wav(tmp_path, duration_ms=1000, filename="short.wav")
        detector = LanguageDetector()
        result = detector.detect(short_audio)
        assert result is None

    @pytest.mark.slow
    @patch.object(LanguageDetector, "_load_model")
    def test_detect_russian(self, mock_load, tmp_path):
        """Should detect Russian from Cyrillic text (requires model download)."""
        long_audio = _make_wav(tmp_path, duration_ms=15000, filename="long.wav")
        detector = LanguageDetector()
        detector._pipe = Mock(return_value={"text": "привет мир"})
        result = detector.detect(long_audio)
        assert result == "ru"

    @pytest.mark.slow
    @patch.object(LanguageDetector, "_load_model")
    def test_detect_english(self, mock_load, tmp_path):
        """Should detect English from non-Cyrillic text (requires model download)."""
        long_audio = _make_wav(tmp_path, duration_ms=15000, filename="long.wav")
        detector = LanguageDetector()
        detector._pipe = Mock(return_value={"text": "hello world"})
        result = detector.detect(long_audio)
        assert result == "en"

    def test_is_russian(self, tmp_path):
        """is_russian should return True only for Russian."""
        short_audio = _make_wav(tmp_path, duration_ms=1000, filename="short.wav")
        detector = LanguageDetector()
        assert detector.is_russian(short_audio) is False


class TestGigaamAudioTranscriber:
    """Tests for GigaamAudioTranscriber."""

    def test_init_defaults(self):
        """Should initialize with default parameters."""
        transcriber = GigaamAudioTranscriber()
        assert transcriber.version == "v3"
        assert transcriber.device == "auto"
        assert transcriber.fp16_encoder is True
        assert transcriber.chunk_length == 25
        assert transcriber.chunk_shift == 20
        assert transcriber.pause_threshold == 0.5

    def test_approximate_word_timestamps(self):
        """Should distribute words evenly across chunk."""
        transcriber = GigaamAudioTranscriber()
        text = "word1 word2 word3"
        words = transcriber._approximate_word_timestamps(text, 0.0, 3.0)
        assert len(words) == 3
        assert words[0]["start"] == 0.0
        assert words[0]["end"] == 1.0
        assert words[1]["start"] == 1.0
        assert words[1]["end"] == 2.0

    def test_merge_words_to_segments(self):
        """Should merge words by pause threshold."""
        transcriber = GigaamAudioTranscriber(pause_threshold=0.5)
        words = [
            {"text": "hello", "start": 0.0, "end": 0.5},
            {"text": "world", "start": 0.6, "end": 1.0},
            {"text": "new", "start": 2.0, "end": 2.5},
            {"text": "sentence", "start": 2.6, "end": 3.0},
        ]
        segments = transcriber._merge_words_to_segments(words)
        assert len(segments) == 2
        assert segments[0]["text"] == "hello world"
        assert segments[1]["text"] == "new sentence"

    def test_merge_words_empty(self):
        """Should handle empty word list."""
        transcriber = GigaamAudioTranscriber()
        segments = transcriber._merge_words_to_segments([])
        assert segments == []

    def test_chunked_trims_overlap_and_emits_chunk_segments(self, tmp_path):
        """Chunked path should trim overlap edges and emit one segment per window."""
        class _FakeAudio:
            """Minimal AudioSegment stand-in (pydub is mocked in conftest)."""

            def __init__(self, ms):
                self._ms = ms

            def __len__(self):
                return self._ms

            def __getitem__(self, _):
                return self

            def set_frame_rate(self, _):
                return self

            def set_channels(self, _):
                return self

            def export(self, path, format=None):
                with open(path, "wb") as fh:
                    fh.write(b"")

        transcriber = GigaamAudioTranscriber(chunk_length=25, chunk_shift=20)
        transcriber._model = Mock()
        # Distinct words per chunk to detect duplication/trimming
        transcriber._model.transcribe = Mock(
            side_effect=[
                " ".join(f"a{i}" for i in range(10)),
                " ".join(f"b{i}" for i in range(10)),
                " ".join(f"g{i}" for i in range(10)),
            ]
        )

        fake_audio = _FakeAudio(50_000)
        with patch(
            "EchoInStone.processing.gigaam_audio_transcriber.AudioSegment"
        ) as mock_as:
            mock_as.from_file.return_value = fake_audio
            text, timestamps = transcriber.transcribe(str(tmp_path / "long.wav"))

        # 50s audio with 25/20 windows → 3 windows (0-25, 20-45, 40-50)
        assert len(timestamps) == 3
        assert transcriber._model.transcribe.call_count == 3
        # No duplicated words across chunk boundaries: each word appears once
        words = text.split()
        assert len(words) == len(set(words)), "duplicate words across chunk overlap"
        # Segments are ordered and within audio duration
        assert timestamps[0]["timestamp"][0] == 0.0
        assert timestamps[-1]["timestamp"][1] <= 50.0
        for i in range(1, len(timestamps)):
            assert timestamps[i]["timestamp"][0] >= timestamps[i - 1]["timestamp"][0]

    def test_load_model_import_error(self):
        """Should raise ImportError if gigaam not installed."""
        with patch.dict("sys.modules", {"gigaam": None}):
            transcriber = GigaamAudioTranscriber()
            with pytest.raises(ImportError):
                transcriber._load_model()


class TestCreateTranscriber:
    """Tests for create_transcriber with gigaam backend."""

    def test_create_gigaam_backend(self):
        """Should create GigaamAudioTranscriber when backend='gigaam'."""
        from main import create_transcriber
        transcriber = create_transcriber("gigaam")
        assert isinstance(transcriber, GigaamAudioTranscriber)

    def test_create_gigaam_fallback_when_not_installed(self):
        """Should fall back to transformers when gigaam not available."""
        from main import create_transcriber
        with patch("main.GigaamAudioTranscriber", None):
            transcriber = create_transcriber("gigaam")
            from EchoInStone.processing import WhisperAudioTranscriber
            assert isinstance(transcriber, WhisperAudioTranscriber)
