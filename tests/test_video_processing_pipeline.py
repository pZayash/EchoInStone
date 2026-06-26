import os

import numpy as np
import pytest

from EchoInStone.processing.keyframe_types import KeyframeRecord, TriggerEvent, merge_trigger_events
from EchoInStone.processing.video_processing_pipeline import VideoProcessingPipeline
from EchoInStone.processing.video_scene_analyzer_interface import SceneSegment
from EchoInStone.processing.ocr_text_extractor_interface import OCRResult


class DummySceneAnalyzer:
    def __init__(self, scenes):
        self.scenes = scenes

    def detect_scenes(self, _video_path):
        return self.scenes


class DummyOCRExtractor:
    def extract_text(self, _image):
        return OCRResult(text="demo text", confidence=0.9, engine="dummy")


class DummyKeyframeExtractor:
    def __init__(self, keyframes=None):
        self.keyframes = keyframes or []
        self.last_kwargs = {}

    def extract_keyframes(self, video_path, output_dir=None, **kwargs):
        self.last_kwargs = kwargs
        return list(self.keyframes)


class DummySaver:
    def __init__(self):
        self.output_dir = "/tmp/job"
        self.enrichment = None

    def save_data(self, *_args, **_kwargs):
        return None

    def save_visual_enrichment(self, entries):
        self.enrichment = entries


def test_build_scene_record_includes_frame_count():
    scene = SceneSegment(id=1, start_time=0.0, end_time=10.0, start_frame=0, end_frame=300)
    record = VideoProcessingPipeline._build_scene_record(
        scene,
        "Scene description",
        "discussion",
        OCRResult(text="hello", confidence=0.8, engine="dummy"),
    )

    assert record["frame_count"] == 300
    assert record["extracted_text"] == "hello"


def test_describe_scene_returns_category():
    frame = np.full((120, 160, 3), 200, dtype=np.uint8)
    description, category = VideoProcessingPipeline._describe_scene(frame)

    assert description
    assert category in {"presentation", "detailed", "dark", "discussion"}


def test_describe_scene_dark_category():
    frame = np.full((120, 160, 3), 10, dtype=np.uint8)
    _description, category = VideoProcessingPipeline._describe_scene(frame)

    assert category in {"dark", "discussion", "presentation"}


def test_analyze_returns_empty_when_no_keyframes(tmp_path):
    analyzer = DummySceneAnalyzer([])
    saver = DummySaver()
    saver.output_dir = str(tmp_path)
    pipeline = VideoProcessingPipeline(
        analyzer,
        DummyOCRExtractor(),
        saver,
        keyframe_extractor=DummyKeyframeExtractor([]),
    )

    scenes, enrichment = pipeline.analyze("video.mp4")

    assert scenes == []
    assert enrichment == []


def test_analyze_runs_ocr_on_keyframes(tmp_path, monkeypatch):
    scenes = [SceneSegment(id=1, start_time=0.0, end_time=2.0, start_frame=0, end_frame=60)]
    keyframes = [
        KeyframeRecord(
            id="abc12345",
            timestamp_seconds=0.0,
            trigger="phrase_timestamp",
            image_path="keyframes/0_phrase_timestamp_abc12345.png",
            created_at="2026-01-01T00:00:00+00:00",
        )
    ]
    saver = DummySaver()
    saver.output_dir = str(tmp_path)
    os.makedirs(tmp_path / "keyframes", exist_ok=True)

    pipeline = VideoProcessingPipeline(
        DummySceneAnalyzer(scenes),
        DummyOCRExtractor(),
        saver,
        keyframe_extractor=DummyKeyframeExtractor(keyframes),
        enable_parallel=False,
    )

    def fake_ocr_sequential(keyframes, _video_path):
        for record in keyframes:
            result = pipeline.ocr_extractor.extract_text(
                np.zeros((20, 20, 3), dtype=np.uint8)
            )
            record.ocr_text = result.text
            record.ocr_confidence = result.confidence
            record.ocr_engine = result.engine

    monkeypatch.setattr(pipeline, "_ocr_sequential", fake_ocr_sequential)

    scene_results, enrichment = pipeline.analyze(
        "video.mp4",
        phrase_timestamps=[0.0],
        include_scene_boundary=False,
        include_periodic=False,
    )

    assert keyframes[0].ocr_text == "demo text"
    assert enrichment
    assert scene_results[0]["extracted_text"] == "demo text"


def test_merge_trigger_events_dedup_and_cap():
    events = [
        TriggerEvent(0.0, "periodic_fallback"),
        TriggerEvent(0.3, "scene_boundary"),
        TriggerEvent(45.0, "periodic_fallback"),
        TriggerEvent(100.0, "phrase_timestamp"),
    ]
    merged = merge_trigger_events(events, dedup_seconds=0.5, max_count=2)
    assert len(merged) == 2
    assert merged[0].trigger == "scene_boundary"
    assert merged[1].trigger == "phrase_timestamp"
