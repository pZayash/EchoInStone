"""Factory for OCR text extractor implementations."""

from __future__ import annotations

import logging

from ..config import OCR_ENGINE
from .easyocr_text_extractor import EasyOCRTextExtractor
from .ocr_text_extractor_interface import OCRTextExtractorInterface
from .tesseract_ocr_text_extractor import TesseractOCRTextExtractor

logger = logging.getLogger(__name__)


def create_ocr_extractor(engine: str | None = None, **kwargs) -> OCRTextExtractorInterface:
    """
    Create an OCR extractor based on configuration.

    Args:
        engine: Override OCR_ENGINE config (`easyocr` or `tesseract`).
        **kwargs: Passed to the extractor constructor.
    """
    selected = (engine or OCR_ENGINE or "easyocr").lower()
    if selected == "tesseract":
        logger.info("Using Tesseract OCR engine.")
        return TesseractOCRTextExtractor(**kwargs)
    if selected == "easyocr":
        logger.info("Using EasyOCR scene-text engine.")
        return EasyOCRTextExtractor(**kwargs)
    logger.warning("Unknown OCR engine %r; defaulting to easyocr.", selected)
    return EasyOCRTextExtractor(**kwargs)
