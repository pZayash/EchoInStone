from EchoInStone.processing.media_processing_orchestrator import MediaProcessingOrchestrator


class DummyAudioPipeline:
    def __init__(self):
        self.called = False

    def process(self, echo_input: str):
        self.called = True
        return ["audio_result"]


class DummyVideoPipeline:
    def __init__(self):
        self.called_with = None

    def analyze(self, video_path: str):
        self.called_with = video_path
        return [{"id": 1}]


def test_media_orchestrator_audio_only():
    audio_pipeline = DummyAudioPipeline()
    orchestrator = MediaProcessingOrchestrator(audio_pipeline=audio_pipeline)

    audio_results, video_results = orchestrator.process("input")

    assert audio_pipeline.called is True
    assert audio_results == ["audio_result"]
    assert video_results is None


def test_media_orchestrator_video_enabled_with_pipeline():
    audio_pipeline = DummyAudioPipeline()
    video_pipeline = DummyVideoPipeline()
    orchestrator = MediaProcessingOrchestrator(
        audio_pipeline=audio_pipeline,
        video_pipeline=video_pipeline,
        enable_video_analysis=True,
    )

    audio_results, video_results = orchestrator.process("input", "video.mp4")

    assert audio_results == ["audio_result"]
    assert video_results == [{"id": 1}]
    assert video_pipeline.called_with == "video.mp4"


def test_media_orchestrator_ignores_invalid_audio_items():
    class MixedAudioPipeline:
        def process(self, _echo_input: str):
            return [
                ("Speaker 1", 0.0, 1.0, "hello"),
                ["Speaker 2", 1.0, 2.0, "world"],
                "invalid",
            ]

    class SceneVideoPipeline:
        def analyze(self, _video_path: str):
            return [{"id": 1, "start_time": 0.0, "end_time": 2.0}]

    orchestrator = MediaProcessingOrchestrator(
        audio_pipeline=MixedAudioPipeline(),
        video_pipeline=SceneVideoPipeline(),
        enable_video_analysis=True,
    )

    _, video_results = orchestrator.process("input", "video.mp4")

    assert video_results[0]["audio_segments"] == [
        {
            "speaker": "Speaker 1",
            "start": 0.0,
            "end": 1.0,
            "overlap_seconds": 1.0,
            "text": "hello",
        }
    ]
