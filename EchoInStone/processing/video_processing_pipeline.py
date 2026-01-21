import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import cv2
import numpy as np

from ..config import (
    VIDEO_FRAME_SAMPLING_SECONDS,
    VIDEO_MAX_SCENE_SAMPLES,
    VIDEO_MAX_WORKERS,
    VIDEO_ENABLE_PARALLEL,
)
from ..utils import DataSaver
from .ocr_text_extractor_interface import OCRResult, OCRTextExtractorInterface
from .video_scene_analyzer_interface import SceneSegment, VideoSceneAnalyzerInterface

logger = logging.getLogger(__name__)


class VideoProcessingPipeline:
    def __init__(self,
                 scene_analyzer: VideoSceneAnalyzerInterface,
                 ocr_extractor: OCRTextExtractorInterface,
                 saver: DataSaver,
                 frame_sampling_seconds: float | None = None,
                 max_workers: int | None = None,
                 enable_parallel: bool | None = None,
                 max_scene_samples: int | None = None):
        self.scene_analyzer = scene_analyzer
        self.ocr_extractor = ocr_extractor
        self.saver = saver
        self.frame_sampling_seconds = (
            frame_sampling_seconds if frame_sampling_seconds is not None else VIDEO_FRAME_SAMPLING_SECONDS
        )
        self.max_workers = max_workers if max_workers is not None else VIDEO_MAX_WORKERS
        self.enable_parallel = enable_parallel if enable_parallel is not None else VIDEO_ENABLE_PARALLEL
        self.max_scene_samples = max_scene_samples if max_scene_samples is not None else VIDEO_MAX_SCENE_SAMPLES

    def analyze(self, video_path: str) -> List[dict]:
        scenes = self.scene_analyzer.detect_scenes(video_path)
        if not scenes:
            logger.warning("No scenes detected for video analysis.")
            return []

        if self.enable_parallel and self.max_workers and self.max_workers > 1:
            return self._analyze_parallel(video_path, scenes)

        cap = cv2.VideoCapture(video_path)
        results: List[dict] = []
        try:
            for scene in scenes:
                results.append(self._analyze_scene(cap, scene))
        finally:
            cap.release()

        return results

    def save_results(self, filename: str, scenes: List[dict]):
        payload = {"scenes": scenes}
        self.saver.save_data(filename, payload)

    def _analyze_parallel(self, video_path: str, scenes: List[SceneSegment]) -> List[dict]:
        results_by_id: dict[int, dict] = {}
        scenes_by_id = {scene.id: scene for scene in scenes}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._analyze_scene_with_path, video_path, scene): scene.id
                for scene in scenes
            }
            for future in futures:
                scene_id = futures[future]
                try:
                    results_by_id[scene_id] = future.result()
                except Exception as exc:
                    logger.warning("Scene analysis failed for scene %s: %s", scene_id, exc)
                    scene = scenes_by_id.get(scene_id)
                    if not scene:
                        continue
                    results_by_id[scene_id] = self._build_scene_record(
                        scene,
                        "Scene analysis failed",
                        "error",
                        OCRResult(text="", confidence=0.0, engine="none"),
                    )

        return [results_by_id[scene.id] for scene in scenes if scene.id in results_by_id]

    def _analyze_scene_with_path(self, video_path: str, scene: SceneSegment) -> dict:
        cap = cv2.VideoCapture(video_path)
        try:
            return self._analyze_scene(cap, scene)
        finally:
            cap.release()

    def _analyze_scene(self, cap, scene: SceneSegment) -> dict:
        frames = self._sample_frames(cap, scene)
        representative_frame = frames[0] if frames else None
        description, category = self._describe_scene(representative_frame)
        ocr_result = self._extract_best_ocr(frames)
        record = self._build_scene_record(scene, description, category, ocr_result)
        frames.clear()
        return record

    def _sample_frames(self, cap, scene: SceneSegment) -> List[np.ndarray]:
        if scene.duration <= 0:
            return []

        sample_step = max(self.frame_sampling_seconds, 0.0)
        if sample_step == 0.0:
            sample_times = [scene.start_time + (scene.duration / 2)]
        else:
            sample_times = []
            current = scene.start_time
            while current <= scene.end_time:
                sample_times.append(current)
                current += sample_step
            if not sample_times:
                sample_times.append(scene.start_time + (scene.duration / 2))

        max_samples = max(1, int(self.max_scene_samples))
        if len(sample_times) > max_samples:
            stride = max(1, len(sample_times) // max_samples)
            sample_times = sample_times[::stride][:max_samples]

        frames: List[np.ndarray] = []
        for sample_time in sample_times:
            cap.set(cv2.CAP_PROP_POS_MSEC, sample_time * 1000)
            ret, frame = cap.read()
            if not ret:
                logger.debug("Failed to read frame for scene %s at %.2fs", scene.id, sample_time)
                continue
            frames.append(frame)

        if not frames:
            midpoint = scene.start_time + (scene.duration / 2)
            cap.set(cv2.CAP_PROP_POS_MSEC, midpoint * 1000)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)

        return frames

    def _extract_best_ocr(self, frames: List[np.ndarray]) -> OCRResult:
        if not frames:
            return OCRResult(text="", confidence=0.0, engine="none")

        best_result = OCRResult(text="", confidence=0.0, engine="none")
        for frame in frames:
            result = self.ocr_extractor.extract_text(frame)
            if result.confidence > best_result.confidence:
                best_result = result
        return best_result

    @staticmethod
    def _describe_scene(frame: Optional[np.ndarray]) -> tuple[str, str]:
        if frame is None:
            return "No frame available", "unknown"

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
    def _build_scene_record(scene: SceneSegment,
                            description: str,
                            category: str,
                            ocr_result: OCRResult) -> dict:
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
