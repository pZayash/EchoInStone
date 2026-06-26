"""Hash-based scene boundary detection for screen-share content."""

from __future__ import annotations

import logging
from typing import List

import cv2
from scenedetect import HashDetector, detect

from ..config import VIDEO_SCENE_HASH_THRESHOLD, KEYFRAME_MIN_BOUNDARIES

logger = logging.getLogger(__name__)


class HashSceneBoundaryDetector:
    """Detect visual change boundaries using PySceneDetect HashDetector."""

    def __init__(self, threshold: float | None = None):
        self.threshold = threshold if threshold is not None else VIDEO_SCENE_HASH_THRESHOLD

    def detect_boundary_times(self, video_path: str) -> List[float]:
        """Return start times (seconds) for each detected boundary."""
        detector = HashDetector(threshold=self.threshold)
        logger.info(
            "Detecting hash boundaries for %s with threshold %.2f",
            video_path,
            self.threshold,
        )
        try:
            scene_list = detect(video_path, detector)
        except Exception as exc:
            logger.warning("Hash boundary detection failed for %s: %s", video_path, exc)
            scene_list = []

        fps = self._get_fps(video_path)
        boundaries: List[float] = []
        for start, _end in scene_list:
            boundaries.append(self._timecode_to_seconds(start, fps))

        duration = self._get_duration(video_path, fps)
        if duration > 600 and len(boundaries) < KEYFRAME_MIN_BOUNDARIES:
            logger.info(
                "Hash detector found %d boundaries on long video; adding SSIM fallback.",
                len(boundaries),
            )
            boundaries = self._ssim_fallback_boundaries(video_path, duration, boundaries)

        if not boundaries and duration > 0:
            boundaries = [0.0]

        logger.info("Hash boundary detection produced %d boundaries.", len(boundaries))
        return sorted(set(boundaries))

    def _ssim_fallback_boundaries(
        self,
        video_path: str,
        duration: float,
        existing: List[float],
    ) -> List[float]:
        """Add coarse SSIM-based boundaries when hash detection is sparse."""
        import numpy as np

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return existing

        sample_interval = 5.0
        prev_gray = None
        boundaries = list(existing)
        current = 0.0

        try:
            while current <= duration:
                cap.set(cv2.CAP_PROP_POS_MSEC, current * 1000)
                ret, frame = cap.read()
                if not ret:
                    break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                small = cv2.resize(gray, (160, 90))
                if prev_gray is not None:
                    diff = cv2.absdiff(small, prev_gray)
                    score = float(np.mean(diff))
                    if score > 8.0 and (not boundaries or current - boundaries[-1] > 2.0):
                        boundaries.append(current)
                prev_gray = small
                current += sample_interval
        finally:
            cap.release()

        return sorted(set(boundaries))

    @staticmethod
    def _get_fps(video_path: str) -> float:
        cap = cv2.VideoCapture(video_path)
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            return fps if fps and fps > 0 else 0.0
        finally:
            cap.release()

    @staticmethod
    def _get_duration(video_path: str, fps: float) -> float:
        cap = cv2.VideoCapture(video_path)
        try:
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if fps and frame_count:
                return float(frame_count) / fps
            return 0.0
        finally:
            cap.release()

    @staticmethod
    def _timecode_to_seconds(timecode, fps: float) -> float:
        if hasattr(timecode, "get_seconds"):
            return float(timecode.get_seconds())
        if fps and getattr(timecode, "frame_num", None) is not None:
            return float(timecode.frame_num / fps)
        return 0.0
