from EchoInStone.processing.audio_processing_orchestrator import AudioProcessingOrchestrator


def test_extract_and_transcribe_returns_tuple_without_media_orchestrator():
    orchestrator = AudioProcessingOrchestrator.__new__(AudioProcessingOrchestrator)
    orchestrator.media_orchestrator = None
    orchestrator.process = lambda echo_input: [("Speaker", 0.0, 1.0, echo_input)]

    result = orchestrator.extract_and_transcribe("input")

    assert isinstance(result, tuple)
    assert len(result) == 2
    assert result[0] == [("Speaker", 0.0, 1.0, "input")]
    assert result[1] is None


def test_extract_and_transcribe_passes_through_media_orchestrator_result():
    orchestrator = AudioProcessingOrchestrator.__new__(AudioProcessingOrchestrator)

    class DummyMediaOrchestrator:
        @staticmethod
        def process(_echo_input, _video_path):
            return ["audio"], [{"scene": 1}]

    orchestrator.media_orchestrator = DummyMediaOrchestrator()

    result = orchestrator.extract_and_transcribe("input", "video.mp4")

    assert result == (["audio"], [{"scene": 1}])
