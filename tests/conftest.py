"""Conftest that pre-mocks heavy ML/GPU dependencies so unit tests can run
without torch, transformers, pydub, pyannote, scenedetect, etc. installed.

This conftest only applies to tests in the tests/ directory.
"""

import sys
from unittest.mock import MagicMock


def _create_mock_torch():
    mock = MagicMock()
    mock.__version__ = "2.7.0"
    mock.xpu.is_available.return_value = False
    mock.xpu.device_count.return_value = 0
    mock.xpu.get_device_name.return_value = "mock"
    mock.cuda.is_available.return_value = False
    mock.backends.mps.is_available.return_value = False
    mock.float16 = "float16"
    mock.float32 = "float32"
    return mock


# Pre-populate sys.modules with mocks for heavy dependencies
# This must happen before any EchoInStone imports
_MOCK_MODULES = {
    "torch": _create_mock_torch(),
    "transformers": MagicMock(),
    "pydub": MagicMock(),
    "pydub.AudioSegment": MagicMock(),
    "pyannote": MagicMock(),
    "pyannote.audio": MagicMock(),
    "pyannote.audio.pipelines": MagicMock(),
    "pyannote.audio.pipelines.utils": MagicMock(),
    "pyannote.audio.pipelines.utils.hook": MagicMock(),
    "scenedetect": MagicMock(),
    "cv2": MagicMock(),
    "pytesseract": MagicMock(),
    "PIL": MagicMock(),
    "PIL.Image": MagicMock(),
    "numpy": MagicMock(),
    "paddleocr": MagicMock(),
    "paddle": MagicMock(),
    "accelerate": MagicMock(),
    "faster_whisper": MagicMock(),
    "yt_dlp": MagicMock(),
    "feedparser": MagicMock(),
}

for mod_name, mock in _MOCK_MODULES.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock
