"""EasyOCR-based scene-text extraction for UI screenshots."""

from __future__ import annotations

import logging
import threading
from typing import List, Optional

from .ocr_text_extractor_interface import OCRResult, OCRTextExtractorInterface
from ..config import EASYOCR_LANGUAGES, OCR_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)

_reader = None
_reader_lock = threading.Lock()
_reader_languages: Optional[tuple[str, ...]] = None


def _get_easyocr_reader(languages: List[str]):
    """Lazy singleton EasyOCR reader."""
    global _reader, _reader_languages
    lang_key = tuple(languages)
    with _reader_lock:
        if _reader is not None and _reader_languages == lang_key:
            return _reader
        try:
            import easyocr
        except ImportError as exc:
            raise ImportError(
                "EasyOCR is not installed. Install with: poetry install --extras scene-ocr"
            ) from exc
        logger.info("Initializing EasyOCR reader (languages=%s, gpu=False)...", languages)
        _reader = easyocr.Reader(languages, gpu=False)
        _reader_languages = lang_key
        logger.info("EasyOCR reader ready.")
        return _reader


class EasyOCRTextExtractor(OCRTextExtractorInterface):
    """Extract on-screen text using EasyOCR (ru+en by default, CPU)."""

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        confidence_threshold: float | None = None,
    ):
        self.languages = languages if languages is not None else list(EASYOCR_LANGUAGES)
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else OCR_CONFIDENCE_THRESHOLD
        )

    def extract_text(self, image) -> OCRResult:
        if image is None:
            return OCRResult(text="", confidence=0.0, engine="none")

        try:
            reader = _get_easyocr_reader(self.languages)
        except ImportError as exc:
            logger.error("%s", exc)
            return OCRResult(text="", confidence=0.0, engine="easyocr")

        try:
            results = reader.readtext(image)
        except Exception as exc:
            logger.warning("EasyOCR failed: %s", exc)
            return OCRResult(text="", confidence=0.0, engine="easyocr")

        texts: List[str] = []
        confidences: List[float] = []
        for item in results:
            if len(item) >= 3:
                text, confidence = item[1], float(item[2])
                if text and text.strip():
                    texts.append(text.strip())
                    confidences.append(confidence * 100.0)

        combined = "\n".join(texts)
        avg_confidence = (sum(confidences) / len(confidences)) if confidences else 0.0
        return OCRResult(text=combined, confidence=avg_confidence, engine="easyocr")
