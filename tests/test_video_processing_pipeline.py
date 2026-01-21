import numpy as np

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


class DummySaver:
    def save_data(self, *_args, **_kwargs):
        return None


def test_build_scene_record_includes_frame_count():
    scene = SceneSegment(id=1, start_time=0.0, end_time=10.0, start_frame=0, end_frame=300)
    record = VideoProcessingPipeline._build_scene_record(
        scene,
        "Scene description",
        "discussion",
        OCRResult(text="hello", confidence=0.8, engine="dummy"),
    )

    assert record["frame_count"] == 300
    assert record["description"] == "Scene description"
    assert record["extracted_text"] == "hello"


def test_describe_scene_returns_category():
    frame = np.full((120, 160, 3), 200, dtype=np.uint8)
    description, category = VideoProcessingPipeline._describe_scene(frame)

    assert description
    assert category in {"presentation", "detailed", "dark", "discussion"}


def test_describe_scene_dark_category():
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    _description, category = VideoProcessingPipeline._describe_scene(frame)

    assert category == "dark"


def test_describe_scene_handles_high_resolution_frame():
    frame = np.full((1080, 1920, 3), 180, dtype=np.uint8)
    description, category = VideoProcessingPipeline._describe_scene(frame)

    assert description
    assert category in {"presentation", "detailed", "dark", "discussion"}


def test_parallel_analysis_preserves_scene_order(monkeypatch):
    scenes = [
        SceneSegment(id=1, start_time=0.0, end_time=2.0, start_frame=0, end_frame=60),
        SceneSegment(id=2, start_time=2.0, end_time=4.0, start_frame=60, end_frame=120),
    ]
    analyzer = DummySceneAnalyzer(scenes)
    pipeline = VideoProcessingPipeline(
        analyzer,
        DummyOCRExtractor(),
        DummySaver(),
        enable_parallel=True,
        max_workers=2,
    )

    def _fake_analyze_scene_with_path(_video_path, scene):
        return {
            "id": scene.id,
            "start_time": scene.start_time,
            "end_time": scene.end_time,
            "duration": scene.duration,
            "start_frame": scene.start_frame,
            "end_frame": scene.end_frame,
            "frame_count": scene.end_frame - scene.start_frame,
            "description": "stub",
            "category": "stub",
            "extracted_text": "",
            "ocr_confidence": 0.0,
            "ocr_engine": "none",
        }

    monkeypatch.setattr(pipeline, "_analyze_scene_with_path", _fake_analyze_scene_with_path)

    results = pipeline.analyze("video.mp4")

    assert [result["id"] for result in results] == [1, 2]


def test_analyze_returns_empty_when_no_scenes():
    analyzer = DummySceneAnalyzer([])
    pipeline = VideoProcessingPipeline(
        analyzer,
        DummyOCRExtractor(),
        DummySaver(),
        enable_parallel=False,
    )

    assert pipeline.analyze("video.mp4") == []


def test_sample_frames_respects_max_samples():
    class DummyCap:
        def __init__(self, frame):
            self.frame = frame

        def set(self, *_args):
            return True

        def read(self):
            return True, self.frame

    analyzer = DummySceneAnalyzer([
        SceneSegment(id=1, start_time=0.0, end_time=10.0, start_frame=0, end_frame=300),
    ])
    pipeline = VideoProcessingPipeline(
        analyzer,
        DummyOCRExtractor(),
        DummySaver(),
        frame_sampling_seconds=1.0,
        max_scene_samples=3,
    )

    frames = pipeline._sample_frames(DummyCap(np.zeros((20, 20, 3), dtype=np.uint8)), analyzer.scenes[0])

    assert len(frames) <= 3
