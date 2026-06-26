import json
import os

import pytest

from EchoInStone.processing.keyframe_types import KeyframeManifest, KeyframeRecord, utc_now_iso


def test_keyframe_manifest_append_and_save(tmp_path):
    manifest_path = tmp_path / "keyframes" / "manifest.json"
    manifest = KeyframeManifest(str(manifest_path))
    record = KeyframeRecord(
        id="kf000001",
        timestamp_seconds=10.0,
        trigger="phrase_timestamp",
        image_path="keyframes/10000_phrase_timestamp_kf000001.png",
        ocr_text="hello",
        ocr_confidence=90.0,
        ocr_engine="easyocr",
        created_at=utc_now_iso(),
    )
    manifest.append(record)
    manifest.save()

    with open(manifest_path, encoding="utf-8") as handle:
        payload = json.load(handle)
    assert len(payload["keyframes"]) == 1
    assert payload["keyframes"][0]["ocr_text"] == "hello"


def test_keyframe_manifest_merge_skips_duplicates(tmp_path):
    manifest_path = tmp_path / "keyframes" / "manifest.json"
    os.makedirs(tmp_path / "keyframes", exist_ok=True)
    manifest = KeyframeManifest(str(manifest_path))
    first = KeyframeRecord(
        id="kf000001",
        timestamp_seconds=10.0,
        trigger="phrase_timestamp",
        created_at=utc_now_iso(),
    )
    duplicate = KeyframeRecord(
        id="kf000002",
        timestamp_seconds=10.0,
        trigger="phrase_timestamp",
        created_at=utc_now_iso(),
    )
    manifest.merge_records([first, duplicate])
    assert len(manifest.keyframes) == 1
