"""Tests for transcriber backend selection, configuration, and faster-whisper integration.

Heavy dependencies are mocked by conftest.py.
"""

import sys
from unittest.mock import patch, MagicMock
import pytest

from EchoInStone.processing.faster_whisper_audio_transcriber import FasterWhisperAudioTranscriber
from EchoInStone.processing.whisper_audio_transcriber import WhisperAudioTranscriber
from main import create_transcriber


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeSegment:
    """Mimics a faster-whisper segment object."""
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text


class FakeTranscriptionInfo:
    def __init__(self, language="en", language_probability=0.98):
        self.language = language
        self.language_probability = language_probability


def _make_transcriber_with_mock_model(segments, info=None):
    """Create a FasterWhisperAudioTranscriber with a mocked model."""
    if info is None:
        info = FakeTranscriptionInfo()
    mock_model = MagicMock()
    mock_model.transcribe.return_value = (iter(segments), info)

    transcriber = FasterWhisperAudioTranscriber.__new__(FasterWhisperAudioTranscriber)
    transcriber.model = mock_model
    return transcriber


# ---------------------------------------------------------------------------
# 6.1: FasterWhisperAudioTranscriber output format conversion
# ---------------------------------------------------------------------------

def test_faster_whisper_output_format_conversion():
    """Verify segments are converted to (text, timestamps) format."""
    segments = [
        FakeSegment(0.0, 2.5, " Hello world "),
        FakeSegment(2.5, 5.0, " This is a test "),
    ]
    transcriber = _make_transcriber_with_mock_model(segments)
    text, timestamps = transcriber.transcribe("dummy.wav")

    assert text == "Hello world This is a test"
    assert len(timestamps) == 2
    assert timestamps[0] == {"timestamp": (0.0, 2.5), "text": "Hello world"}
    assert timestamps[1] == {"timestamp": (2.5, 5.0), "text": "This is a test"}


def test_faster_whisper_empty_segments_filtered():
    """Verify empty/whitespace-only segments are filtered out."""
    segments = [
        FakeSegment(0.0, 1.0, "  "),
        FakeSegment(1.0, 3.0, " Actual content "),
        FakeSegment(3.0, 4.0, ""),
    ]
    transcriber = _make_transcriber_with_mock_model(segments)
    text, timestamps = transcriber.transcribe("dummy.wav")

    assert text == "Actual content"
    assert len(timestamps) == 1


def test_faster_whisper_transcribe_error_returns_none():
    """Verify transcribe returns (None, None) on error."""
    mock_model = MagicMock()
    mock_model.transcribe.side_effect = RuntimeError("model error")

    transcriber = FasterWhisperAudioTranscriber.__new__(FasterWhisperAudioTranscriber)
    transcriber.model = mock_model

    text, timestamps = transcriber.transcribe("dummy.wav")
    assert text is None
    assert timestamps is None


# ---------------------------------------------------------------------------
# 6.2: Backend auto-selection logic
# ---------------------------------------------------------------------------

def test_auto_select_transformers_when_xpu_available():
    """Auto-selection should choose transformers when Intel XPU is available."""
    mock_torch = sys.modules["torch"]
    original = mock_torch.xpu.is_available.return_value
    mock_torch.xpu.is_available.return_value = True
    try:
        result = create_transcriber("auto")
        assert isinstance(result, WhisperAudioTranscriber)
    finally:
        mock_torch.xpu.is_available.return_value = original


def test_auto_select_faster_whisper_when_no_xpu():
    """Auto-selection should choose faster-whisper when no XPU is available."""
    mock_torch = sys.modules["torch"]
    original = mock_torch.xpu.is_available.return_value
    mock_torch.xpu.is_available.return_value = False
    try:
        result = create_transcriber("auto")
        assert isinstance(result, FasterWhisperAudioTranscriber)
    finally:
        mock_torch.xpu.is_available.return_value = original


def test_explicit_transformers_backend():
    """Explicit 'transformers' backend should use WhisperAudioTranscriber."""
    result = create_transcriber("transformers")
    assert isinstance(result, WhisperAudioTranscriber)


def test_explicit_faster_whisper_backend():
    """Explicit 'faster-whisper' backend should use FasterWhisperAudioTranscriber."""
    result = create_transcriber("faster-whisper")
    assert isinstance(result, FasterWhisperAudioTranscriber)


# ---------------------------------------------------------------------------
# 6.3: batch_size configuration in WhisperAudioTranscriber
# ---------------------------------------------------------------------------

def test_batch_size_parameter_exists():
    """WhisperAudioTranscriber should accept batch_size as constructor parameter."""
    import inspect
    sig = inspect.signature(WhisperAudioTranscriber.__init__)
    assert "batch_size" in sig.parameters
    assert sig.parameters["batch_size"].default is None


def test_batch_size_stored_from_config():
    """WhisperAudioTranscriber should use WHISPER_BATCH_SIZE from config when batch_size is None."""
    transcriber = WhisperAudioTranscriber()
    assert transcriber.batch_size == 24


def test_batch_size_custom_override():
    """WhisperAudioTranscriber should use custom batch_size when provided."""
    transcriber = WhisperAudioTranscriber(batch_size=8)
    assert transcriber.batch_size == 8


# ---------------------------------------------------------------------------
# 6.5: Graceful fallback when faster-whisper is not installed
# ---------------------------------------------------------------------------

def test_fallback_when_faster_whisper_not_installed():
    """create_transcriber should fall back to transformers when faster-whisper is unavailable."""
    import main
    original = main.FasterWhisperAudioTranscriber
    main.FasterWhisperAudioTranscriber = None
    try:
        result = create_transcriber("faster-whisper")
        assert isinstance(result, WhisperAudioTranscriber)
    finally:
        main.FasterWhisperAudioTranscriber = original


def test_faster_whisper_import_error_raises_informative_message():
    """FasterWhisperAudioTranscriber should raise ImportError with install instructions."""
    from EchoInStone.processing import faster_whisper_audio_transcriber as mod

    original = mod._FASTER_WHISPER_AVAILABLE
    mod._FASTER_WHISPER_AVAILABLE = False
    try:
        with pytest.raises(ImportError, match="faster-whisper is not installed"):
            mod.FasterWhisperAudioTranscriber()
    finally:
        mod._FASTER_WHISPER_AVAILABLE = original
