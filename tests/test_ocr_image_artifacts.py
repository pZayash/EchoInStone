import json

import numpy as np

from EchoInStone.processing.tesseract_ocr_text_extractor import TesseractOCRTextExtractor
from EchoInStone.utils.data_saver import DataSaver


def test_save_image_artifact_writes_manifest(tmp_path):
    saver = DataSaver(output_dir=str(tmp_path))
    image = np.zeros((16, 16, 3), dtype=np.uint8)

    filename = saver.save_image_artifact(
        job_id=None,
        scene_id=1,
        image=image,
        engine="tesseract",
        variant="psm3_gray",
        preprocessing=["grayscale"],
        ocr_confidence=0.55,
        text_excerpt="hello world",
        max_per_scene=5,
        image_format="png",
    )

    assert filename is not None
    artifact_dir = tmp_path / "ocr_screenshots" / "scene_1"
    assert artifact_dir.exists()
    assert list(artifact_dir.glob("*.png"))

    manifest_path = tmp_path / "ocr_screenshots" / "manifest.json"
    assert manifest_path.exists()
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    assert manifest["images"]
    entry = manifest["images"][0]
    assert entry["scene_id"] == 1
    assert entry["engine"] == "tesseract"


def test_ocr_artifact_disabled_skips_write(tmp_path, monkeypatch):
    saver = DataSaver(output_dir=str(tmp_path))
    image = np.zeros((8, 8, 3), dtype=np.uint8)

    extractor = TesseractOCRTextExtractor(
        data_saver=saver,
        job_id=None,
        scene_id=2,
    )

    monkeypatch.setattr(
        "EchoInStone.processing.tesseract_ocr_text_extractor.OCR_SAVE_SOURCE_IMAGES_ENABLED",
        False,
    )
    extractor._maybe_save_artifact(
        image=image,
        engine="tesseract",
        variant="psm6",
        preprocessing=[],
        ocr_confidence=0.2,
        text_excerpt="skip",
    )

    assert not (tmp_path / "ocr_screenshots").exists()
