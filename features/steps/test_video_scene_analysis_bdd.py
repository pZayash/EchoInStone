import pytest
from pytest_bdd import given, scenarios, then, when

from EchoInStone.processing.media_processing_orchestrator import MediaProcessingOrchestrator

scenarios("../video_scene_analysis.feature")


class DummyAudioPipeline:
    def __init__(self):
        self.called = False

    def process(self, _echo_input):
        self.called = True
        return ["audio_result"]


class DummyVideoPipeline:
    def __init__(self):
        self.called_with = None

    def analyze(self, video_path):
        self.called_with = video_path
        return [{"id": 1}]


@pytest.fixture
def media_orchestrator_context():
    audio_pipeline = DummyAudioPipeline()
    video_pipeline = DummyVideoPipeline()
    orchestrator = MediaProcessingOrchestrator(
        audio_pipeline=audio_pipeline,
        video_pipeline=video_pipeline,
        enable_video_analysis=True,
    )
    return {
        "orchestrator": orchestrator,
        "audio_pipeline": audio_pipeline,
        "video_pipeline": video_pipeline,
        "video_path": "demo.mp4",
    }


@given("a media orchestrator with video analysis enabled")
def media_orchestrator_context_setup(media_orchestrator_context):
    return media_orchestrator_context


@when("processing input with a video path")
def process_input(media_orchestrator_context):
    orchestrator = media_orchestrator_context["orchestrator"]
    video_path = media_orchestrator_context["video_path"]
    media_orchestrator_context["result"] = orchestrator.process("input", video_path)


@then("the video pipeline is invoked")
def video_pipeline_invoked(media_orchestrator_context):
    video_pipeline = media_orchestrator_context["video_pipeline"]
    assert video_pipeline.called_with == media_orchestrator_context["video_path"]
