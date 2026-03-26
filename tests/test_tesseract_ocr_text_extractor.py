import os
import numpy as np
import pytesseract

from EchoInStone.processing.ocr_text_extractor_interface import OCRResult
from EchoInStone.processing.tesseract_ocr_text_extractor import TesseractOCRTextExtractor


def test_ocr_caches_results(monkeypatch):
    call_count = {"count": 0}

    def fake_image_to_data(_image, lang=None, output_type=None):
        call_count["count"] += 1
        return {
            "text": ["Hello"],
            "conf": ["92"],
        }

    monkeypatch.setattr(pytesseract, "image_to_data", fake_image_to_data)

    monkeypatch.setattr(TesseractOCRTextExtractor, "_ensure_tesseract_available", lambda _self: True)
    extractor = TesseractOCRTextExtractor(
        confidence_threshold=10.0,
        use_paddle_fallback=False,
    )
    image = np.zeros((20, 20, 3), dtype=np.uint8)

    first = extractor.extract_text(image)
    second = extractor.extract_text(image)

    assert first.text == "Hello"
    assert second.text == "Hello"
    assert call_count["count"] == 1


def test_ocr_filters_low_confidence(monkeypatch):
    def fake_image_to_data(_image, lang=None, output_type=None):
        return {
            "text": ["Low"],
            "conf": ["5"],
        }

    monkeypatch.setattr(pytesseract, "image_to_data", fake_image_to_data)

    monkeypatch.setattr(TesseractOCRTextExtractor, "_ensure_tesseract_available", lambda _self: True)
    extractor = TesseractOCRTextExtractor(
        confidence_threshold=20.0,
        use_paddle_fallback=False,
    )
    image = np.zeros((20, 20, 3), dtype=np.uint8)

    result = extractor.extract_text(image)

    assert result.text == ""
    assert result.confidence == 5.0


def test_ocr_uses_paddle_fallback_on_low_confidence(monkeypatch):
    def fake_image_to_data(_image, lang=None, output_type=None):
        return {
            "text": ["Low"],
            "conf": ["5"],
        }

    monkeypatch.setattr(pytesseract, "image_to_data", fake_image_to_data)
    monkeypatch.setattr(TesseractOCRTextExtractor, "_ensure_tesseract_available", lambda _self: True)
    monkeypatch.setattr(
        TesseractOCRTextExtractor,
        "_extract_with_paddle",
        lambda _self, _image: OCRResult(text="Fallback", confidence=80.0, engine="paddleocr"),
    )

    extractor = TesseractOCRTextExtractor(
        confidence_threshold=20.0,
        use_paddle_fallback=True,
    )
    image = np.zeros((20, 20, 3), dtype=np.uint8)

    result = extractor.extract_text(image)

    assert result.text == "Fallback"
    assert result.engine == "paddleocr"


def test_paddle_home_configuration(monkeypatch, tmp_path):
    monkeypatch.delenv("PADDLE_HOME", raising=False)
    extractor = TesseractOCRTextExtractor(
        confidence_threshold=20.0,
        use_paddle_fallback=True,
        paddle_model_dir=str(tmp_path / "paddle_models"),
    )
    extractor._configure_paddle_home()

    assert "PADDLE_HOME" in os.environ
    assert os.environ["PADDLE_HOME"] == str(tmp_path / "paddle_models")


def test_paddle_ocr_call_without_cls(monkeypatch):
    class FakeOCR:
        def ocr(self, image):
            return [[[None, ("hello", 0.9)]]]

    extractor = TesseractOCRTextExtractor(use_paddle_fallback=True)
    extractor._paddle_ocr = FakeOCR()

    result = extractor._call_paddle_ocr("image")

    assert result
