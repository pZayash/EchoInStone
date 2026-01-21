import numpy as np
import pytesseract

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

    extractor = TesseractOCRTextExtractor(
        confidence_threshold=20.0,
        use_paddle_fallback=False,
    )
    image = np.zeros((20, 20, 3), dtype=np.uint8)

    result = extractor.extract_text(image)

    assert result.text == ""
    assert result.confidence == 5.0
