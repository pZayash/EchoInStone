import logging
from typing import List

import cv2
from scenedetect import ContentDetector, detect

from .video_scene_analyzer_interface import SceneSegment, VideoSceneAnalyzerInterface
from ..config import VIDEO_SCENE_DETECTOR_THRESHOLD

logger = logging.getLogger(__name__)


class PySceneDetectVideoSceneAnalyzer(VideoSceneAnalyzerInterface):
    def __init__(self, threshold: float | None = None):
        self.threshold = threshold if threshold is not None else VIDEO_SCENE_DETECTOR_THRESHOLD

    def detect_scenes(self, video_path: str) -> List[SceneSegment]:
        detector = ContentDetector(threshold=self.threshold)
        try:
            scene_list = detect(video_path, detector)
        except Exception as exc:
            logger.warning("Scene detection failed for %s: %s", video_path, exc)
            scene_list = []

        fps = self._get_fps(video_path)
        scenes: List[SceneSegment] = []
        for index, (start, end) in enumerate(scene_list, start=1):
            start_seconds = self._timecode_to_seconds(start, fps)
            end_seconds = self._timecode_to_seconds(end, fps)
            scenes.append(
                SceneSegment(
                    id=index,
                    start_time=start_seconds,
                    end_time=end_seconds,
                    start_frame=start.frame_num,
                    end_frame=end.frame_num,
                )
            )

        if not scenes:
            logger.info("No scene boundaries detected; treating entire video as one scene.")
            total_frames = self._get_frame_count(video_path)
            duration = (total_frames / fps) if fps and total_frames else 0.0
            scenes.append(
                SceneSegment(
                    id=1,
                    start_time=0.0,
                    end_time=duration,
                    start_frame=0,
                    end_frame=total_frames,
                )
            )

        return scenes

    @staticmethod
    def _get_fps(video_path: str) -> float:
        cap = cv2.VideoCapture(video_path)
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            return fps if fps and fps > 0 else 0.0
        finally:
            cap.release()

    @staticmethod
    def _get_frame_count(video_path: str) -> int:
        cap = cv2.VideoCapture(video_path)
        try:
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            return int(frame_count) if frame_count else 0
        finally:
            cap.release()

    @staticmethod
    def _timecode_to_seconds(timecode, fps: float) -> float:
        if hasattr(timecode, "get_seconds"):
            return float(timecode.get_seconds())
        if fps and getattr(timecode, "frame_num", None) is not None:
            return float(timecode.frame_num / fps)
        return 0.0
