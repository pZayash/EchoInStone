# processing/__init__.py

from .audio_transcriber_interface import AudioTranscriberInterface
from .diarizer_interface import DiarizerInterface
from .aligner_interface import AlignerInterface
from .whisper_audio_transcriber import WhisperAudioTranscriber
from .pyannote_diarizer import PyannoteDiarizer
from .speaker_aligner import SpeakerAligner
from .audio_processing_orchestrator import AudioProcessingOrchestrator
from .audio_processing_pipeline import AudioProcessingPipeline
from .media_processing_orchestrator import MediaProcessingOrchestrator
from .video_processing_pipeline import VideoProcessingPipeline
from .video_scene_analyzer_interface import VideoSceneAnalyzerInterface, SceneSegment
from .ocr_text_extractor_interface import OCRTextExtractorInterface, OCRResult
from .py_scene_detect_video_scene_analyzer import PySceneDetectVideoSceneAnalyzer
from .tesseract_ocr_text_extractor import TesseractOCRTextExtractor

try:
    from .faster_whisper_audio_transcriber import FasterWhisperAudioTranscriber
except ImportError:
    FasterWhisperAudioTranscriber = None

__all__ = [
    'AudioTranscriberInterface',
    'DiarizerInterface',
    'AlignerInterface',
    'WhisperAudioTranscriber',
    'PyannoteDiarizer',
    'SpeakerAligner',
    'AudioProcessingOrchestrator',
    'AudioProcessingPipeline',
    'MediaProcessingOrchestrator',
    'VideoProcessingPipeline',
    'VideoSceneAnalyzerInterface',
    'SceneSegment',
    'OCRTextExtractorInterface',
    'OCRResult',
    'PySceneDetectVideoSceneAnalyzer',
    'TesseractOCRTextExtractor',
    'FasterWhisperAudioTranscriber',
]
