"""Extract keyframes from video at combined trigger points."""

from __future__ import annotations

import logging
import os
from typing import List, Optional

import cv2
import numpy as np

from ..config import (
    KEYFRAME_DEDUP_SECONDS,
    KEYFRAME_MAX_PER_JOB,
    KEYFRAME_PERIODIC_INTERVAL_SECONDS,
    KEYFRAME_SAVE_ENABLED,
)
from .hash_scene_boundary_detector import HashSceneBoundaryDetector
from .keyframe_types import (
    TRIGGER_PERIODIC_FALLBACK,
    TRIGGER_PHRASE_TIMESTAMP,
    TRIGGER_SCENE_BOUNDARY,
    KeyframeRecord,
    TriggerEvent,
    merge_trigger_events,
    new_keyframe_id,
    utc_now_iso,
)

logger = logging.getLogger(__name__)


class KeyframeExtractor:
    """Collect triggers, capture frames, optionally persist PNG artifacts."""

    def __init__(
        self,
        boundary_detector: Optional[HashSceneBoundaryDetector] = None,
        periodic_interval_seconds: float | None = None,
        dedup_seconds: float | None = None,
        max_keyframes: int | None = None,
        save_enabled: bool | None = None,
    ):
        self.boundary_detector = boundary_detector or HashSceneBoundaryDetector()
        self.periodic_interval_seconds = (
            periodic_interval_seconds
            if periodic_interval_seconds is not None
            else KEYFRAME_PERIODIC_INTERVAL_SECONDS
        )
        self.dedup_seconds = dedup_seconds if dedup_seconds is not None else KEYFRAME_DEDUP_SECONDS
        self.max_keyframes = max_keyframes if max_keyframes is not None else KEYFRAME_MAX_PER_JOB
        self.save_enabled = save_enabled if save_enabled is not None else KEYFRAME_SAVE_ENABLED

    def collect_triggers(
        self,
        video_path: str,
        phrase_timestamps: Optional[List[float]] = None,
        include_scene_boundary: bool = True,
        include_periodic: bool = True,
    ) -> List[TriggerEvent]:
        """Build deduplicated trigger list without capturing frames."""
        events: List[TriggerEvent] = []
        duration = self._get_duration(video_path)

        if include_scene_boundary:
            for ts in self.boundary_detector.detect_boundary_times(video_path):
                events.append(TriggerEvent(timestamp_seconds=ts, trigger=TRIGGER_SCENE_BOUNDARY))

        if include_periodic and self.periodic_interval_seconds > 0 and duration > 0:
            current = 0.0
            while current <= duration:
                events.append(
                    TriggerEvent(timestamp_seconds=current, trigger=TRIGGER_PERIODIC_FALLBACK)
                )
                current += self.periodic_interval_seconds

        if phrase_timestamps:
            for ts in phrase_timestamps:
                events.append(
                    TriggerEvent(timestamp_seconds=ts, trigger=TRIGGER_PHRASE_TIMESTAMP)
                )

        merged = merge_trigger_events(events, self.dedup_seconds, self.max_keyframes)
        if len(events) > len(merged):
            logger.warning(
                "Capped keyframe triggers from %d to %d (max=%d).",
                len(events),
                len(merged),
                self.max_keyframes,
            )
        return merged

    def extract_keyframes(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        phrase_timestamps: Optional[List[float]] = None,
        include_scene_boundary: bool = True,
        include_periodic: bool = True,
    ) -> List[KeyframeRecord]:
        """Capture frames at trigger timestamps and return keyframe records."""
        triggers = self.collect_triggers(
            video_path,
            phrase_timestamps=phrase_timestamps,
            include_scene_boundary=include_scene_boundary,
            include_periodic=include_periodic,
        )
        if not triggers:
            return []

        keyframes_dir = None
        if output_dir and self.save_enabled:
            keyframes_dir = os.path.join(output_dir, "keyframes")
            os.makedirs(keyframes_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Cannot open video for keyframe extraction: %s", video_path)
            return []

        records: List[KeyframeRecord] = []
        try:
            for event in triggers:
                frame = self._read_frame_at(cap, event.timestamp_seconds)
                if frame is None:
                    logger.debug("Failed to read frame at %.2fs", event.timestamp_seconds)
                    continue

                record_id = new_keyframe_id()
                image_path = None
                if keyframes_dir:
                    ms = int(round(event.timestamp_seconds * 1000))
                    filename = f"{ms}_{event.trigger}_{record_id}.png"
                    filepath = os.path.join(keyframes_dir, filename)
                    cv2.imwrite(filepath, frame)
                    image_path = os.path.join("keyframes", filename)

                records.append(
                    KeyframeRecord(
                        id=record_id,
                        timestamp_seconds=event.timestamp_seconds,
                        trigger=event.trigger,
                        image_path=image_path,
                        created_at=utc_now_iso(),
                        triggers=[event.trigger],
                    )
                )
                frame = None
        finally:
            cap.release()

        logger.info("Extracted %d keyframes from %s", len(records), video_path)
        return records

    @staticmethod
    def _read_frame_at(cap: cv2.VideoCapture, timestamp_seconds: float) -> Optional[np.ndarray]:
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, timestamp_seconds) * 1000)
        ret, frame = cap.read()
        return frame if ret else None

    @staticmethod
    def _get_duration(video_path: str) -> float:
        cap = cv2.VideoCapture(video_path)
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if fps and fps > 0 and frame_count:
                return float(frame_count) / float(fps)
            return 0.0
        finally:
            cap.release()
