import logging
import tempfile
import os
from typing import Optional

from pydub import AudioSegment

from .audio_transcriber_interface import AudioTranscriberInterface
from EchoInStone.utils.torch_device import resolve_torch_device

logger = logging.getLogger(__name__)

# GigaAM chunking parameters (per design)
CHUNK_LENGTH_SECONDS = 25
CHUNK_SHIFT_SECONDS = 20
PAUSE_THRESHOLD_SECONDS = 0.5


class GigaamAudioTranscriber(AudioTranscriberInterface):
    """GigaAM v3 CTC backend for Russian-language transcription."""

    def __init__(
        self,
        version: str = "v3",
        device: str = "auto",
        fp16_encoder: bool = True,
        chunk_length: int = CHUNK_LENGTH_SECONDS,
        chunk_shift: int = CHUNK_SHIFT_SECONDS,
        pause_threshold: float = PAUSE_THRESHOLD_SECONDS,
    ):
        self.version = version
        self.device = device
        self.fp16_encoder = fp16_encoder
        self.chunk_length = chunk_length
        self.chunk_shift = chunk_shift
        self.pause_threshold = pause_threshold
        self._model = None
        self._device_resolved: Optional[str] = None

    def _resolve_device(self) -> str:
        if self.device != "auto":
            return self.device
        resolved = resolve_torch_device()
        return str(resolved)

    def _load_model(self):
        if self._model is not None:
            return
        try:
            import gigaam
        except ImportError as exc:
            raise ImportError(
                "gigaam is not installed. Install it with: "
                "poetry install --extras gigaam"
            ) from exc

        self._device_resolved = self._resolve_device()
        logger.info(f"Loading GigaAM {self.version} CTC on {self._device_resolved}")

        try:
            self._model = gigaam.load_model(
                f"{self.version}_ctc",
                fp16_encoder=self.fp16_encoder,
                device=self._device_resolved,
            )
            self._model.eval()
        except Exception as exc:
            logger.error(f"Failed to load GigaAM model: {exc}")
            raise

    def transcribe(self, audio_path: str) -> tuple:
        """Transcribe audio using GigaAM v3 CTC.

        Args:
            audio_path: Path to the audio file.

        Returns:
            tuple: (full_text, timestamps) where timestamps are ASR chunks.
        """
        self._load_model()

        try:
            audio = AudioSegment.from_file(audio_path)
            duration_seconds = len(audio) / 1000.0
        except Exception as exc:
            logger.error(f"Failed to load audio: {exc}")
            return None, None

        logger.info(f"Audio duration: {duration_seconds:.1f}s")

        # For short audio, transcribe directly
        if duration_seconds <= self.chunk_length:
            return self._transcribe_short(audio_path)

        # Chunked transcription for long audio
        return self._transcribe_chunked(audio_path, audio, duration_seconds)

    def _extract_text(self, result) -> str:
        """Extract text from GigaAM TranscriptionResult."""
        if isinstance(result, str):
            return result
        if hasattr(result, "text"):
            return result.text or ""
        return str(result)

    def _transcribe_short(self, audio_path: str) -> tuple:
        """Transcribe audio ≤ chunk_length directly."""
        logger.info("Transcribing short audio directly")
        try:
            result = self._model.transcribe(audio_path)
            text = self._extract_text(result)
            duration = self._get_audio_duration(audio_path)
            timestamps = [{"timestamp": (0.0, duration), "text": text.strip()}]
            return text.strip(), timestamps
        except Exception as exc:
            logger.error(f"GigaAM transcription failed: {exc}")
            return None, None

    def _transcribe_chunked(self, audio_path: str, audio: AudioSegment, duration: float) -> tuple:
        """Transcribe long audio in overlapping chunks.

        Emits one ASR chunk per transcription window (chunk-level segments) so
        SpeakerAligner receives multiple segments and diarization works.
        Overlapping edges are trimmed (~half of the overlap on each side) to
        avoid duplicated text at chunk boundaries.
        """
        logger.info(f"Chunked transcription: chunk={self.chunk_length}s shift={self.chunk_shift}s")

        overlap = max(self.chunk_length - self.chunk_shift, 0)
        overlap_half = overlap / 2.0

        segments = []
        chunk_start = 0.0

        while chunk_start < duration:
            chunk_end = min(chunk_start + self.chunk_length, duration)
            is_first = chunk_start == 0.0
            is_last = chunk_end >= duration
            logger.debug(f"Processing chunk {chunk_start:.1f}s - {chunk_end:.1f}s")

            chunk_audio = audio[int(chunk_start * 1000):int(chunk_end * 1000)]
            chunk_audio = chunk_audio.set_frame_rate(16000).set_channels(1)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                chunk_audio.export(tmp.name, format="wav")
                tmp_path = tmp.name

            try:
                result = self._model.transcribe(tmp_path)
                text = self._extract_text(result)
                words = self._approximate_word_timestamps(text, chunk_start, chunk_end)

                if not is_first and overlap_half > 0:
                    words = [w for w in words if w["start"] >= chunk_start + overlap_half]
                if not is_last and overlap_half > 0:
                    words = [w for w in words if w["end"] <= chunk_end - overlap_half]

                if words:
                    segments.append({
                        "start": words[0]["start"],
                        "end": words[-1]["end"],
                        "text": " ".join(w["text"] for w in words),
                    })
            except Exception as exc:
                logger.error(f"Chunk transcription failed: {exc}")
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

            chunk_start += self.chunk_shift

        full_text = " ".join(seg["text"] for seg in segments)
        timestamps = [
            {"timestamp": (seg["start"], seg["end"]), "text": seg["text"]}
            for seg in segments
        ]

        logger.info(f"Transcription completed: {len(timestamps)} chunks")
        return full_text, timestamps

    def _get_audio_duration(self, audio_path: str) -> float:
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0

    def _approximate_word_timestamps(self, text: str, chunk_start: float, chunk_end: float) -> list:
        """Approximate word timestamps by distributing evenly across chunk."""
        words = text.strip().split()
        if not words:
            return []
        duration = chunk_end - chunk_start
        word_duration = duration / len(words)
        result = []
        for i, word in enumerate(words):
            start = chunk_start + i * word_duration
            end = start + word_duration
            result.append({"text": word, "start": start, "end": end})
        return result

    def _merge_words_to_segments(self, words: list) -> list:
        """Merge words into segments by pause threshold."""
        if not words:
            return []
        segments = [[words[0]]]
        for i in range(1, len(words)):
            gap = words[i]["start"] - words[i - 1]["end"]
            if gap > self.pause_threshold:
                segments.append([words[i]])
            else:
                segments[-1].append(words[i])
        result = []
        for seg_words in segments:
            result.append({
                "start": seg_words[0]["start"],
                "end": seg_words[-1]["end"],
                "text": " ".join(w["text"] for w in seg_words),
            })
        return result
