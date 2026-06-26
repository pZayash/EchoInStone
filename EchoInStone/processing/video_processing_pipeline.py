import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import cv2

from ..config import VIDEO_ENABLE_PARALLEL, VIDEO_MAX_WORKERS
from ..utils import DataSaver
from .hash_scene_boundary_detector import HashSceneBoundaryDetector
from .keyframe_extractor import KeyframeExtractor
from .keyframe_types import KeyframeManifest, KeyframeRecord
from .ocr_text_extractor_interface import OCRResult, OCRTextExtractorInterface
from .video_scene_analyzer_interface import SceneSegment, VideoSceneAnalyzerInterface

logger = logging.getLogger(__name__)


class VideoProcessingPipeline:
    """Extract keyframes, run scene-text OCR, and produce enrichment artifacts."""

    def __init__(
        self,
        scene_analyzer: VideoSceneAnalyzerInterface,
        ocr_extractor: OCRTextExtractorInterface,
        saver: DataSaver,
        keyframe_extractor: Optional[KeyframeExtractor] = None,
        job_id: str | None = None,
        max_workers: int | None = None,
        enable_parallel: bool | None = None,
    ):
        self.scene_analyzer = scene_analyzer
        self.ocr_extractor = ocr_extractor
        self.saver = saver
        self.keyframe_extractor = keyframe_extractor or KeyframeExtractor(
            boundary_detector=HashSceneBoundaryDetector()
        )
        self.job_id = job_id
        self.max_workers = max_workers if max_workers is not None else VIDEO_MAX_WORKERS
        self.enable_parallel = enable_parallel if enable_parallel is not None else VIDEO_ENABLE_PARALLEL

    def analyze(
        self,
        video_path: str,
        phrase_timestamps: Optional[List[float]] = None,
        include_scene_boundary: bool = True,
        include_periodic: bool = True,
    ) -> tuple[List[dict], List[dict]]:
        """
        Run keyframe extraction + OCR and return (scene_records, enrichment_entries).
        """
        logger.info("Running video visual analysis on %s", video_path)
        keyframes = self.keyframe_extractor.extract_keyframes(
            video_path,
            output_dir=self.saver.output_dir,
            phrase_timestamps=phrase_timestamps,
            include_scene_boundary=include_scene_boundary,
            include_periodic=include_periodic,
        )
        if not keyframes:
            logger.warning("No keyframes extracted for %s", video_path)
            return [], []

        if self.enable_parallel and self.max_workers and self.max_workers > 1:
            self._ocr_parallel(keyframes, video_path)
        else:
            self._ocr_sequential(keyframes, video_path)

        manifest_path = os.path.join(self.saver.output_dir, "keyframes", "manifest.json")
        manifest = KeyframeManifest(manifest_path)
        manifest.merge_records(keyframes)
        manifest.save()

        enrichment_entries = manifest.to_enrichment_entries()
        self.saver.save_visual_enrichment(enrichment_entries)

        scenes = self.scene_analyzer.detect_scenes(video_path)
        scene_records = self._build_scene_records(scenes, keyframes)
        logger.info(
            "Video analysis produced %d keyframes and %d scene records.",
            len(keyframes),
            len(scene_records),
        )
        return scene_records, enrichment_entries

    def save_results(self, filename: str, scenes: List[dict]):
        payload = {"scenes": scenes}
        self.saver.save_data(filename, payload)

    def _ocr_sequential(self, keyframes: List[KeyframeRecord], video_path: str) -> None:
        cap = cv2.VideoCapture(video_path)
        try:
            for record in keyframes:
                frame = KeyframeExtractor._read_frame_at(cap, record.timestamp_seconds)
                if frame is None and record.image_path:
                    frame = self._load_saved_frame(record.image_path)
                if frame is None:
                    continue
                result = self.ocr_extractor.extract_text(frame)
                record.ocr_text = result.text
                record.ocr_confidence = result.confidence
                record.ocr_engine = result.engine
        finally:
            cap.release()

    def _ocr_parallel(self, keyframes: List[KeyframeRecord], video_path: str) -> None:
        def process(record: KeyframeRecord) -> KeyframeRecord:
            cap = cv2.VideoCapture(video_path)
            try:
                frame = KeyframeExtractor._read_frame_at(cap, record.timestamp_seconds)
            finally:
                cap.release()
            if frame is None and record.image_path:
                frame = self._load_saved_frame(record.image_path)
            if frame is None:
                return record
            result = self.ocr_extractor.extract_text(frame)
            record.ocr_text = result.text
            record.ocr_confidence = result.confidence
            record.ocr_engine = result.engine
            return record

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            processed = list(executor.map(process, keyframes))
        keyframes[:] = processed

    def _load_saved_frame(self, relative_path: str):
        path = os.path.join(self.saver.output_dir, relative_path)
        if not os.path.isfile(path):
            return None
        return cv2.imread(path)

    def _build_scene_records(
        self, scenes: List[SceneSegment], keyframes: List[KeyframeRecord]
    ) -> List[dict]:
        records: List[dict] = []
        keyframe_by_time = {round(k.timestamp_seconds, 2): k for k in keyframes}

        for scene in scenes:
            start_key = round(scene.start_time, 2)
            kf = keyframe_by_time.get(start_key)
            if kf is None:
                for candidate in keyframes:
                    if scene.start_time <= candidate.timestamp_seconds <= scene.end_time:
                        kf = candidate
                        break

            description, category = self._describe_scene_from_keyframe(kf)
            ocr_result = OCRResult(
                text=kf.ocr_text if kf else "",
                confidence=kf.ocr_confidence if kf else 0.0,
                engine=kf.ocr_engine if kf else "none",
            )
            records.append(
                self._build_scene_record(scene, description, category, ocr_result)
            )
        return records

    def _describe_scene_from_keyframe(self, keyframe: Optional[KeyframeRecord]) -> tuple[str, str]:
        if keyframe is None or not keyframe.image_path:
            return "No keyframe available", "unknown"
        frame = self._load_saved_frame(keyframe.image_path)
        return self._describe_scene(frame)

    @staticmethod
    def _describe_scene(frame) -> tuple[str, str]:
        if frame is None:
            return "No frame available", "unknown"

        import numpy as np

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        edges = cv2.Canny(gray, 100, 200)
        edge_density = float(np.count_nonzero(edges)) / float(edges.size)
        color_variance = float(np.var(frame))

        if edge_density > 0.06 and color_variance < 500.0:
            return "Presentation-style slide with dense edges", "presentation"
        if edge_density > 0.06:
            return "Detailed visual scene with text or graphics", "detailed"
        if brightness < 40.0:
            return "Dark scene with low visibility", "dark"
        return "Simple scene or talking head", "discussion"

    @staticmethod
    def _build_scene_record(
        scene: SceneSegment,
        description: str,
        category: str,
        ocr_result: OCRResult,
    ) -> dict:
        frame_count = max(0, scene.end_frame - scene.start_frame)
        return {
            "id": scene.id,
            "start_time": scene.start_time,
            "end_time": scene.end_time,
            "duration": scene.duration,
            "start_frame": scene.start_frame,
            "end_frame": scene.end_frame,
            "frame_count": frame_count,
            "description": description,
            "category": category,
            "extracted_text": ocr_result.text,
            "ocr_confidence": ocr_result.confidence,
            "ocr_engine": ocr_result.engine,
        }
