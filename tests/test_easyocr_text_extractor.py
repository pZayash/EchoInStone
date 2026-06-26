import numpy as np
import pytest

easyocr = pytest.importorskip("easyocr", reason="easyocr not installed (poetry install --extras scene-ocr)")

from EchoInStone.processing.easyocr_text_extractor import EasyOCRTextExtractor


def test_easyocr_extract_text_on_synthetic_image():
    extractor = EasyOCRTextExtractor(languages=["en"])
    image = np.full((100, 300, 3), 255, dtype=np.uint8)
    result = extractor.extract_text(image)
    assert result.engine == "easyocr"
    assert result.confidence >= 0.0
