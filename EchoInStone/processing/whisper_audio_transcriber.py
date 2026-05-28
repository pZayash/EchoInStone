import logging
import threading
import time
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from pydub import AudioSegment
from .audio_transcriber_interface import AudioTranscriberInterface
from EchoInStone.utils import timer, log_time
from EchoInStone.config import WHISPER_BATCH_SIZE
from EchoInStone.utils.torch_device import log_accelerator_info, resolve_whisper_device

logger = logging.getLogger(__name__)

class WhisperAudioTranscriber(AudioTranscriberInterface):
    def __init__(self, model_name="openai/whisper-large-v3-turbo", batch_size=None):
        """Initialize the WhisperAudioTranscriber with the specified model.

        Args:
            model_name (str): The name of the model to use for transcription.
        """
        log_accelerator_info(logger)
        self.device, self.torch_dtype = resolve_whisper_device()

        self.batch_size = batch_size if batch_size is not None else WHISPER_BATCH_SIZE

        logger.info(f"Using device: {self.device} with dtype: {self.torch_dtype}")

        # Load the model and processor
        try:
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_name,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            )
            self.model.to(self.device)

            self.processor = AutoProcessor.from_pretrained(model_name)

            # Configure the pipeline for automatic speech recognition
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                torch_dtype=self.torch_dtype,
                device=self.device,
                #model_kwargs={"attn_implementation": "sdpa"},
                return_timestamps=True,  # or "word"
                batch_size=self.batch_size,
                generate_kwargs={"max_new_tokens": 400},
                chunk_length_s=5,
                stride_length_s=(1, 1),
            )
            logger.info("Transcription model and pipeline loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading the transcription model: {e}")
            raise

    def _get_audio_duration(self, audio_path: str) -> float:
        """Get the duration of the audio file in seconds.

        Args:
            audio_path (str): Path to the audio file.

        Returns:
            float: Duration in seconds, or 0 if unable to determine.
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            duration_seconds = len(audio) / 1000.0  # pydub returns duration in milliseconds
            return duration_seconds
        except Exception as e:
            logger.warning(f"Could not determine audio duration: {e}")
            return 0.0

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to a human-readable string.

        Args:
            seconds (float): Duration in seconds.

        Returns:
            str: Formatted duration string (e.g., "5m 30s" or "1h 23m 45s").
        """
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

    def _progress_logger(self, duration: float, stop_event: threading.Event):
        """Log progress periodically while transcription is running.

        Args:
            duration (float): Audio duration in seconds, or 0 if unknown.
            stop_event (threading.Event): Event to signal when to stop logging.
        """
        start_time = time.time()
        interval = 60  # Log every 1 minute
        last_logged = 0
        
        while not stop_event.is_set():
            elapsed = time.time() - start_time
            if elapsed - last_logged >= interval:
                elapsed_str = self._format_duration(elapsed)
                if duration > 0:
                    # Show elapsed time and ratio to audio duration
                    # Processing typically takes longer than audio duration
                    ratio = elapsed / duration
                    logger.info(f"Transcription in progress... elapsed: {elapsed_str} "
                              f"(processing time / audio duration: {ratio:.2f}x)")
                else:
                    logger.info(f"Transcription in progress... elapsed: {elapsed_str}")
                last_logged = elapsed
            time.sleep(1)

    @timer
    def transcribe(self, audio_path: str) -> tuple:
        """Transcribe audio from the given file path.

        Args:
            audio_path (str): Path to the audio file to transcribe.

        Returns:
            tuple: A tuple containing the transcription text and timestamps.
        """
        try:
            # Get audio duration for progress tracking
            duration = self._get_audio_duration(audio_path)
            chunk_length = self.pipe.chunk_length_s if hasattr(self.pipe, 'chunk_length_s') else 5
            
            if duration > 0:
                estimated_chunks = int(duration / chunk_length) + 1
                duration_str = self._format_duration(duration)
                logger.info(f"Starting transcription of {audio_path}")
                logger.info(f"Audio duration: {duration_str} ({duration:.1f}s), estimated chunks: {estimated_chunks}")
            else:
                logger.info(f"Starting transcription of {audio_path}")
                logger.info("Audio duration: unknown")

            # Start progress logger in background thread
            stop_event = threading.Event()
            progress_thread = threading.Thread(
                target=self._progress_logger,
                args=(duration, stop_event),
                daemon=True
            )
            progress_thread.start()

            # Perform transcription with timestamps
            logger.info("Transcription in progress...")
            try:
                result = self.pipe(audio_path)
                transcription = result['text']
                timestamps = result['chunks']
            finally:
                # Stop progress logger
                stop_event.set()
                progress_thread.join(timeout=1)
            
            # Log completion with statistics
            if timestamps:
                processed_chunks = len(timestamps)
                transcription_length = len(transcription) if transcription else 0
                logger.info(f"Transcription completed: processed {processed_chunks} chunks, "
                          f"generated {transcription_length} characters")
            else:
                logger.info("Transcription completed")
            
            logger.info(f"Successfully transcribed: {audio_path}")
            return transcription, timestamps
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None, None
