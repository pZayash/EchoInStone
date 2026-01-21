from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class SceneSegment:
    id: int
    start_time: float
    end_time: float
    start_frame: int
    end_frame: int

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)


class VideoSceneAnalyzerInterface(ABC):
    @abstractmethod
    def detect_scenes(self, video_path: str) -> List[SceneSegment]:
        """Detects scenes in a video and returns structured segments."""
        raise NotImplementedError
