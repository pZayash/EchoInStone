import logging
import threading
import time

from .audio_transcriber_interface import AudioTranscriberInterface
from EchoInStone.config import FASTER_WHISPER_MODEL_SIZE, FASTER_WHISPER_COMPUTE_TYPE

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    _FASTER_WHISPER_AVAILABLE = True
except ImportError:
    _FASTER_WHISPER_AVAILABLE = False


class FasterWhisperAudioTranscriber(AudioTranscriberInterface):
    def __init__(self, model_size=None, compute_type=None):
        """Initialize the FasterWhisperAudioTranscriber.

        Args:
            model_size (str): Model size to use. Defaults to config FASTER_WHISPER_MODEL_SIZE.
            compute_type (str): Compute type. Defaults to config FASTER_WHISPER_COMPUTE_TYPE.
        """
        if not _FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper is not installed. Install it with: "
                "poetry install --extras faster-whisper"
            )

        self.model_size = model_size or FASTER_WHISPER_MODEL_SIZE
        self.compute_type = compute_type or FASTER_WHISPER_COMPUTE_TYPE

        # Auto-detect device
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
                if self.compute_type == "auto":
                    self.compute_type = "float16"
            else:
                self.device = "cpu"
                if self.compute_type == "auto":
                    self.compute_type = "int8"
        except ImportError:
            self.device = "cpu"
            if self.compute_type == "auto":
                self.compute_type = "int8"

        logger.info(f"Loading faster-whisper model: {self.model_size} on {self.device} ({self.compute_type})")
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        logger.info("Faster-whisper model loaded successfully.")

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to a human-readable string."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}h {minutes}m {secs}s"

    def _progress_logger(self, stop_event: threading.Event):
        """Log progress periodically while transcription is running."""
        start_time = time.time()
        interval = 60
        last_logged = 0

        while not stop_event.is_set():
            elapsed = time.time() - start_time
            if elapsed - last_logged >= interval:
                elapsed_str = self._format_duration(elapsed)
                logger.info(f"Transcription in progress... elapsed: {elapsed_str}")
                last_logged = elapsed
            time.sleep(1)

    def transcribe(self, audio_path: str) -> tuple:
        """Transcribe audio using faster-whisper.

        Args:
            audio_path (str): Path to the audio file to transcribe.

        Returns:
            tuple: A tuple containing (text, timestamps) in EchoInStone format.
        """
        try:
            logger.info(f"Starting faster-whisper transcription of {audio_path}")

            # Start progress logger
            stop_event = threading.Event()
            progress_thread = threading.Thread(
                target=self._progress_logger,
                args=(stop_event,),
                daemon=True,
            )
            progress_thread.start()

            try:
                segments, info = self.model.transcribe(
                    audio_path,
                    vad_filter=True,
                )

                logger.info(
                    f"Detected language: {info.language} (probability: {info.language_probability:.2f})"
                )

                # Convert segments to EchoInStone format
                full_text_parts = []
                timestamps = []

                for segment in segments:
                    text = segment.text.strip()
                    if text:
                        full_text_parts.append(text)
                        timestamps.append({
                            "timestamp": (segment.start, segment.end),
                            "text": text,
                        })

                full_text = " ".join(full_text_parts)
            finally:
                stop_event.set()
                progress_thread.join(timeout=1)

            logger.info(
                f"Transcription completed: {len(timestamps)} chunks, "
                f"{len(full_text)} characters"
            )
            logger.info(f"Successfully transcribed: {audio_path}")
            return full_text, timestamps

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None, None
