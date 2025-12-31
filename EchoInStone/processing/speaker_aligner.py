from .aligner_interface import AlignerInterface
import logging

# Import segment splitting configuration
try:
    from ..config import (
        SEGMENT_TARGET_DURATION,
        SEGMENT_MIN_DURATION,
        SEGMENT_MAX_DURATION,
        SEGMENT_PAUSE_THRESHOLD,
    )
except ImportError:
    # Fallback defaults if config is not available
    SEGMENT_TARGET_DURATION = 30
    SEGMENT_MIN_DURATION = 20
    SEGMENT_MAX_DURATION = 60
    SEGMENT_PAUSE_THRESHOLD = 2.0

logger = logging.getLogger(__name__)

class SpeakerAligner(AlignerInterface):
    def align(self, transcription, timestamps, diarization):
        """Aligns the transcription with timestamps and speaker diarization.

        Args:
            transcription (str): The complete text of the transcription.
            timestamps (list): List of text segments with their corresponding timestamps.
            diarization (object): Diarization object containing speaker segments.

        Returns:
            list: List of aligned segments with speaker identifiers and timestamps.
        """
        logger.debug("Combining transcription and diarization...")
        speaker_transcriptions = []

        # Guard against missing diarization or timestamps to avoid None math
        if diarization is None or timestamps is None:
            logger.warning("Cannot align without diarization and timestamps.")
            return speaker_transcriptions

        # Find the end time of the last segment in diarization
        last_segment = self.get_last_segment(diarization)
        last_diarization_end = last_segment.end if last_segment else None

        for chunk in timestamps:
            chunk_start = chunk['timestamp'][0]
            chunk_end = chunk['timestamp'][1]
            segment_text = chunk['text']

            # Skip chunks without a valid start
            if chunk_start is None:
                logger.warning(f"Skipping chunk with missing start time: {chunk}")
                continue

            # Handle the case where chunk_end is None
            if chunk_end is None:
                # Use the end of the last diarization segment as the default end time
                chunk_end = last_diarization_end if last_diarization_end is not None else chunk_start

            # Find the best matching speaker segment
            best_match = self.find_best_match(diarization, chunk_start, chunk_end)
            if best_match:
                speaker = best_match[2]  # Extract the speaker label
                speaker_transcriptions.append((speaker, chunk_start, chunk_end, segment_text))

        # Merge consecutive segments of the same speaker
        speaker_transcriptions = self.merge_consecutive_segments(speaker_transcriptions)
        return speaker_transcriptions

    def find_best_match(self, diarization, start_time, end_time):
        """Finds the best matching speaker segment for a given time range.

        Args:
            diarization (object): Diarization object containing speaker segments.
            start_time (float): Start time of the segment.
            end_time (float): End time of the segment.

        Returns:
            tuple: The best matching speaker segment (start, end, speaker).
        """
        # If timestamps are missing, we cannot compute an overlap
        if start_time is None or end_time is None:
            logger.warning(f"Cannot find match without valid times: start={start_time}, end={end_time}")
            return None

        best_match = None
        max_intersection = 0

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            turn_start = turn.start
            turn_end = turn.end

            # Skip segments with None start or end times
            if turn_start is None or turn_end is None:
                logger.warning(f"Skipping diarization segment with None times: start={turn_start}, end={turn_end}")
                continue

            # Calculate intersection manually
            intersection_start = max(start_time, turn_start)
            intersection_end = min(end_time, turn_end)

            if intersection_start < intersection_end:
                intersection_length = intersection_end - intersection_start
                if intersection_length > max_intersection:
                    max_intersection = intersection_length
                    best_match = (turn_start, turn_end, speaker)

        return best_match

    def _should_split_segment(self, current_segment, next_segment):
        """Determines if segments should NOT be merged based on duration and pauses.

        Split priority:
        1. Pause between segments > SEGMENT_PAUSE_THRESHOLD (2+ seconds)
        2. Current segment >= SEGMENT_TARGET_DURATION and ends with sentence punctuation
        3. Current segment >= SEGMENT_MAX_DURATION (forced split)

        Args:
            current_segment (tuple): Current segment (speaker, start, end, text).
            next_segment (tuple): Next segment (speaker, start, end, text).

        Returns:
            bool: True if segments should NOT be merged (split here).
        """
        current_duration = current_segment[2] - current_segment[1]
        pause_duration = next_segment[1] - current_segment[2]
        text = current_segment[3].strip()

        # 1. Pause longer than threshold - always split
        if pause_duration >= SEGMENT_PAUSE_THRESHOLD:
            logger.debug(f"Splitting due to pause: {pause_duration:.2f}s >= {SEGMENT_PAUSE_THRESHOLD}s")
            return True

        # 2. Target duration reached and text ends with sentence punctuation
        if current_duration >= SEGMENT_TARGET_DURATION:
            # Check for sentence-ending punctuation (including Russian and common patterns)
            sentence_endings = ('.', '?', '!', '...', '。', '？', '！')
            if text.endswith(sentence_endings):
                logger.debug(f"Splitting at sentence end: duration={current_duration:.2f}s, text ends with punctuation")
                return True

        # 3. Maximum duration reached - forced split
        if current_duration >= SEGMENT_MAX_DURATION:
            logger.debug(f"Forced split: duration={current_duration:.2f}s >= {SEGMENT_MAX_DURATION}s")
            return True

        return False

    def merge_consecutive_segments(self, segments):
        """Merges consecutive segments of the same speaker with intelligent splitting.

        Segments are merged unless:
        - Different speaker
        - Pause between segments > SEGMENT_PAUSE_THRESHOLD
        - Current segment duration >= SEGMENT_TARGET_DURATION and ends with sentence
        - Current segment duration >= SEGMENT_MAX_DURATION (forced split)

        Args:
            segments (list): List of segments to merge.

        Returns:
            list: List of merged segments with target duration ~30 seconds.
        """
        merged_segments = []
        previous_segment = None

        for segment in segments:
            if previous_segment is None:
                previous_segment = segment
            else:
                # Check if same speaker
                if segment[0] == previous_segment[0]:
                    # Check if we should split based on duration/pauses
                    if self._should_split_segment(previous_segment, segment):
                        # Don't merge - save previous and start new
                        merged_segments.append(previous_segment)
                        previous_segment = segment
                    else:
                        # Merge segments of the same speaker
                        previous_segment = (
                            previous_segment[0],
                            previous_segment[1],
                            segment[2],
                            previous_segment[3] + segment[3]
                        )
                else:
                    # Different speaker - don't merge
                    merged_segments.append(previous_segment)
                    previous_segment = segment

        if previous_segment:
            merged_segments.append(previous_segment)

        logger.info(f"Merged {len(segments)} segments into {len(merged_segments)} segments")
        return merged_segments

    def get_last_segment(self, annotation):
        """Retrieves the last segment from the annotation.

        Args:
            annotation (object): Annotation object containing segments.

        Returns:
            object: The last segment in the annotation.
        """
        last_segment = None
        for segment in annotation.itersegments():
            last_segment = segment
        return last_segment
