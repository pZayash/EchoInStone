import logging
from typing import Optional

from pydub import AudioSegment
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

from EchoInStone.utils.torch_device import resolve_whisper_device

logger = logging.getLogger(__name__)

LANGUAGE_DETECTOR_MODEL = "openai/whisper-tiny"
DETECTION_AUDIO_SECONDS = 30
MIN_AUDIO_DURATION_SECONDS = 10


class LanguageDetector:
    """Detects the dominant language of an audio file using Whisper tiny."""

    def __init__(self, model_name: str = LANGUAGE_DETECTOR_MODEL):
        self.device, self.torch_dtype = resolve_whisper_device()
        self.model_name = model_name
        self._pipe = None
        logger.info(f"LanguageDetector using device: {self.device}")

    def _load_model(self):
        if self._pipe is not None:
            return
        try:
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

            model = AutoModelForSpeechSeq2Seq.from_pretrained(
                self.model_name,
                torch_dtype=self.torch_dtype,
                low_cpu_mem_usage=True,
                use_safetensors=True,
            )
            model.to(self.device)
            processor = AutoProcessor.from_pretrained(self.model_name)
            self._pipe = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                torch_dtype=self.torch_dtype,
                device=self.device,
            )
        except Exception as exc:
            logger.error(f"Failed to load language detection model: {exc}")
            raise

    def detect(self, audio_path: str) -> Optional[str]:
        """Detect language of the audio file.

        Returns ISO language code (e.g., "ru", "en") or None if audio is too short.
        """
        try:
            audio = AudioSegment.from_file(audio_path)
            duration_seconds = len(audio) / 1000.0
        except Exception as exc:
            logger.error(f"Failed to load audio for language detection: {exc}")
            return None

        if duration_seconds <= MIN_AUDIO_DURATION_SECONDS:
            logger.debug(f"Audio too short for language detection: {duration_seconds:.1f}s")
            return None

        if self._pipe is None:
            self._load_model()

        # Use first DETECTION_AUDIO_SECONDS for detection
        clip = audio[: DETECTION_AUDIO_SECONDS * 1000]
        clip = clip.set_frame_rate(16000).set_channels(1)

        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            clip.export(tmp.name, format="wav")
            tmp_path = tmp.name

        try:
            result = self._pipe(tmp_path, return_timestamps=False)
            language = self._extract_language(result)
            logger.info(f"Detected language: {language} (audio duration: {duration_seconds:.1f}s)")
            return language
        except Exception as exc:
            logger.error(f"Language detection failed: {exc}")
            return None
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _extract_language(self, result) -> Optional[str]:
        """Extract language code from Whisper result."""
        # Whisper pipeline with return_timestamps=False may not expose language directly.
        # We use a fallback: detect based on text characteristics or use model.generate with language token.
        # For now, use a simple heuristic: if text contains Cyrillic, return "ru".
        text = result.get("text", "")
        if any("\u0400" <= c <= "\u04FF" for c in text):
            return "ru"
        if text.strip():
            return "en"
        return None

    def is_russian(self, audio_path: str) -> bool:
        """Return True if detected language is Russian."""
        return self.detect(audio_path) == "ru"
