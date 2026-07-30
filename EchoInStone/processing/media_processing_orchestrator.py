import logging
import re
from typing import Optional, Tuple

from .audio_processing_pipeline import AudioProcessingPipeline
from .video_processing_pipeline import VideoProcessingPipeline

logger = logging.getLogger(__name__)


class MediaProcessingOrchestrator:
    def __init__(self,
                 audio_pipeline: AudioProcessingPipeline,
                 video_pipeline: Optional[VideoProcessingPipeline] = None,
                 enable_video_analysis: bool = False):
        self.audio_pipeline = audio_pipeline
        self.video_pipeline = video_pipeline
        self.enable_video_analysis = enable_video_analysis

    def process(self, echo_input: str, video_path: Optional[str] = None, audio_path: Optional[str] = None) -> Tuple[Optional[list], Optional[list]]:
        audio_results = self.audio_pipeline.process(echo_input, audio_path=audio_path)

        video_results = None
        if self.enable_video_analysis:
            if self.video_pipeline and video_path:
                logger.info("Starting video scene analysis...")
                video_results, _enrichment = self.video_pipeline.analyze(video_path)
                if audio_results and video_results:
                    self._correlate_audio_with_scenes(audio_results, video_results)
            else:
                logger.warning("Video analysis enabled but no video pipeline or video path provided.")

        return audio_results, video_results

    @staticmethod
    def _correlate_audio_with_scenes(audio_results: list, video_results: list) -> None:
        transitions = MediaProcessingOrchestrator._extract_speaker_transitions(audio_results)
        for scene in video_results:
            start_time = scene.get("start_time")
            end_time = scene.get("end_time")
            if start_time is None or end_time is None:
                continue

            overlapping_segments = []
            scene_text_parts = []
            speakers = set()
            for speaker, seg_start, seg_end, text in MediaProcessingOrchestrator._iter_audio_segments(audio_results):
                if seg_start is None or seg_end is None:
                    continue
                overlap_start = max(start_time, seg_start)
                overlap_end = min(end_time, seg_end)
                if overlap_start < overlap_end:
                    overlap = overlap_end - overlap_start
                    overlapping_segments.append(
                        {
                            "speaker": speaker,
                            "start": seg_start,
                            "end": seg_end,
                            "overlap_seconds": overlap,
                            "text": text,
                        }
                    )
                    if speaker:
                        speakers.add(speaker)
                    if text:
                        scene_text_parts.append(text)

            scene["audio_segments"] = overlapping_segments
            scene["speakers"] = sorted(speakers)
            scene["speaker_transitions"] = [
                transition
                for transition in transitions
                if start_time <= transition["time"] <= end_time
            ]

            ocr_text = scene.get("extracted_text") or ""
            audio_text = " ".join(scene_text_parts)
            scene["audio_text_alignment"] = MediaProcessingOrchestrator._compute_text_overlap(
                ocr_text, audio_text
            )

    @staticmethod
    def _extract_speaker_transitions(audio_results: list) -> list:
        transitions = []
        previous_speaker = None
        previous_end = None
        for speaker, start, end, _ in MediaProcessingOrchestrator._iter_audio_segments(audio_results):
            if previous_speaker is not None and speaker != previous_speaker:
                transition_time = start if start is not None else previous_end
                if transition_time is not None:
                    transitions.append(
                        {
                            "time": transition_time,
                            "from_speaker": previous_speaker,
                            "to_speaker": speaker,
                        }
                    )
            previous_speaker = speaker
            previous_end = end
        return transitions

    @staticmethod
    def _iter_audio_segments(audio_results: list) -> list:
        valid_segments = []
        for item in audio_results:
            if isinstance(item, tuple) and len(item) == 4:
                valid_segments.append(item)
            else:
                logger.debug("Skipping invalid audio result item: %s", item)
        return valid_segments

    @staticmethod
    def _compute_text_overlap(ocr_text: str, audio_text: str) -> dict:
        def _tokenize(text: str) -> set[str]:
            return {token for token in re.findall(r"[A-Za-z0-9_]+", text.lower()) if token}

        ocr_tokens = _tokenize(ocr_text)
        audio_tokens = _tokenize(audio_text)

        if not ocr_tokens or not audio_tokens:
            return {"overlap_score": 0.0, "matched_terms": []}

        matched = ocr_tokens & audio_tokens
        score = len(matched) / max(len(ocr_tokens), 1)
        return {"overlap_score": round(score, 3), "matched_terms": sorted(matched)}
