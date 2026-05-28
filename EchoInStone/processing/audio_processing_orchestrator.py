from typing import Optional, Tuple

from .audio_processing_pipeline import AudioProcessingPipeline
from .media_processing_orchestrator import MediaProcessingOrchestrator


class AudioProcessingOrchestrator(AudioProcessingPipeline):
    def __init__(self, *args, media_orchestrator: Optional[MediaProcessingOrchestrator] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.media_orchestrator = media_orchestrator

    def extract_and_transcribe(self, echo_input: str, video_path: Optional[str] = None) -> Tuple[Optional[list], Optional[list]]:
        if self.media_orchestrator:
            return self.media_orchestrator.process(echo_input, video_path)
        return self.process(echo_input), None
