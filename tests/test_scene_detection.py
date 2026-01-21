from types import SimpleNamespace

from EchoInStone.processing.py_scene_detect_video_scene_analyzer import PySceneDetectVideoSceneAnalyzer
from EchoInStone.processing.video_scene_analyzer_interface import SceneSegment


def test_scene_detection_builds_segments(monkeypatch):
    analyzer = PySceneDetectVideoSceneAnalyzer(threshold=15.0)

    class DummyTimecode:
        def __init__(self, frame_num, seconds):
            self.frame_num = frame_num
            self._seconds = seconds

        def get_seconds(self):
            return self._seconds

    dummy_scenes = [
        (DummyTimecode(0, 0.0), DummyTimecode(30, 1.0)),
        (DummyTimecode(30, 1.0), DummyTimecode(60, 2.0)),
    ]

    monkeypatch.setattr(
        "EchoInStone.processing.py_scene_detect_video_scene_analyzer.detect",
        lambda _video_path, _detector: dummy_scenes,
    )
    monkeypatch.setattr(analyzer, "_get_fps", lambda _path: 30.0)

    scenes = analyzer.detect_scenes("demo.mp4")

    assert scenes == [
        SceneSegment(id=1, start_time=0.0, end_time=1.0, start_frame=0, end_frame=30),
        SceneSegment(id=2, start_time=1.0, end_time=2.0, start_frame=30, end_frame=60),
    ]


def test_scene_detection_falls_back_to_single_scene(monkeypatch):
    analyzer = PySceneDetectVideoSceneAnalyzer()

    monkeypatch.setattr(
        "EchoInStone.processing.py_scene_detect_video_scene_analyzer.detect",
        lambda _video_path, _detector: [],
    )
    monkeypatch.setattr(analyzer, "_get_fps", lambda _path: 25.0)
    monkeypatch.setattr(analyzer, "_get_frame_count", lambda _path: 250)

    scenes = analyzer.detect_scenes("demo.mp4")

    assert scenes == [
        SceneSegment(id=1, start_time=0.0, end_time=10.0, start_frame=0, end_frame=250),
    ]


def test_scene_detection_handles_invalid_video(monkeypatch):
    analyzer = PySceneDetectVideoSceneAnalyzer()

    def _raise(_video_path, _detector):
        raise RuntimeError("invalid video")

    monkeypatch.setattr(
        "EchoInStone.processing.py_scene_detect_video_scene_analyzer.detect",
        _raise,
    )
    monkeypatch.setattr(analyzer, "_get_fps", lambda _path: 0.0)
    monkeypatch.setattr(analyzer, "_get_frame_count", lambda _path: 0)

    scenes = analyzer.detect_scenes("broken.mp4")

    assert scenes == [
        SceneSegment(id=1, start_time=0.0, end_time=0.0, start_frame=0, end_frame=0),
    ]
