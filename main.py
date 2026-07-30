import argparse
import os
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

from EchoInStone.utils import configure_logging
import logging

from EchoInStone.capture.downloader_factory import get_downloader, get_video_downloader
from EchoInStone.processing import (
    AudioProcessingPipeline,
    MediaProcessingOrchestrator,
    VideoProcessingPipeline,
    WhisperAudioTranscriber,
    FasterWhisperAudioTranscriber,
    GigaamAudioTranscriber,
    LanguageDetector,
    PyannoteDiarizer,
    SpeakerAligner,
    PySceneDetectVideoSceneAnalyzer,
    HashSceneBoundaryDetector,
    KeyframeExtractor,
    create_ocr_extractor,
    parse_timestamp_list,
)
from EchoInStone.utils import DataSaver
from EchoInStone.utils import timer, log_time
from EchoInStone.config import (
    VIDEO_ANALYSIS_ENABLED,
    VIDEO_ENABLE_PARALLEL,
    VIDEO_MAX_WORKERS,
    OCR_ENGINE,
    SUBTITLE_FIRST_ENABLED,
    TRANSCRIBER_BACKEND,
    GIGAAM_ENABLED,
    GIGAAM_DEVICE,
    GIGAAM_FP16,
    GIGAAM_CHUNK_LENGTH,
    GIGAAM_CHUNK_SHIFT,
    GIGAAM_PAUSE_THRESHOLD,
)

# Configure logging
configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


def extract_input_name(echo_input: str) -> str:
    """
    Extracts a safe filename from the input (URL, local file path, etc.)
    to use in the output directory name.
    """
    if os.path.isfile(echo_input):
        base_name = os.path.basename(echo_input)
        name_without_ext = os.path.splitext(base_name)[0]
        return name_without_ext

    parsed_url = urlparse(echo_input)

    if "youtube.com" in echo_input or "youtu.be" in echo_input:
        try:
            import yt_dlp
            ydl_opts = {
                'quiet': True,
                'js_runtimes': {'node': {}},
                'remote_components': ['ejs:github']
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(echo_input, download=False)
                video_title = info.get('title', None)
            if video_title:
                return video_title
        except Exception as e:
            logger.warning(f"Could not fetch YouTube video title: {e}")

        video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', echo_input)
        if video_id_match:
            return f"youtube_{video_id_match.group(1)}"
        return "youtube_video"

    if echo_input.endswith(".xml"):
        path_parts = [p for p in parsed_url.path.split('/') if p]
        if path_parts:
            return os.path.splitext(path_parts[-1])[0]
        return "podcast"

    if parsed_url.path:
        filename = os.path.basename(parsed_url.path)
        if filename:
            name_without_ext = os.path.splitext(filename)[0]
            if name_without_ext:
                return name_without_ext

    if parsed_url.netloc:
        domain = parsed_url.netloc.replace('.', '_')
        return domain[:50]

    safe_name = re.sub(r'[^\w\s-]', '', echo_input).replace(' ', '_')[:50]
    return safe_name if safe_name else "input"


def sanitize_dir_name(name: str) -> str:
    """Sanitizes a string to be safe for use as a directory name."""
    sanitized = re.sub(r'[<>:"|?*\\]', '', name)
    sanitized = sanitized.strip(' .')
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    return sanitized[:100] if sanitized else "input"


def get_source_info(echo_input: str) -> str:
    """Gets the source information (YouTube URL or filename) for transcription output."""
    if "youtube.com" in echo_input or "youtu.be" in echo_input:
        return echo_input
    if os.path.isfile(echo_input):
        return os.path.basename(echo_input)
    return echo_input


def create_transcriber(backend: str | None = None, audio_path: str | None = None):
    """Create a transcriber instance based on backend selection.

    Args:
        backend: Backend name or None to use config.
        audio_path: Path to audio file for language detection (auto mode only).
    """
    import torch

    if backend is None:
        backend = TRANSCRIBER_BACKEND

    if backend == "auto":
        # Language-aware selection: GigaAM for Russian if installed
        if (
            GIGAAM_ENABLED
            and GigaamAudioTranscriber is not None
            and audio_path is not None
        ):
            detector = LanguageDetector()
            if detector.is_russian(audio_path):
                backend = "gigaam"
                logger.info("Auto-selected 'gigaam' backend (Russian language detected)")
            else:
                backend = "transformers" if torch.xpu.is_available() else "faster-whisper"
                logger.info("Auto-selected Whisper backend (non-Russian or detection skipped)")
        elif torch.xpu.is_available():
            backend = "transformers"
            logger.info("Auto-selected 'transformers' backend (Intel XPU detected)")
        else:
            backend = "faster-whisper"
            logger.info("Auto-selected 'faster-whisper' backend")

    if backend == "gigaam":
        if not GIGAAM_ENABLED or GigaamAudioTranscriber is None:
            logger.warning(
                "gigaam is not installed or disabled. Falling back to transformers backend. "
                "Install with: poetry install --extras gigaam"
            )
            return WhisperAudioTranscriber()
        try:
            return GigaamAudioTranscriber(
                device=GIGAAM_DEVICE,
                fp16_encoder=GIGAAM_FP16,
                chunk_length=GIGAAM_CHUNK_LENGTH,
                chunk_shift=GIGAAM_CHUNK_SHIFT,
                pause_threshold=GIGAAM_PAUSE_THRESHOLD,
            )
        except ImportError:
            logger.warning("gigaam not available. Falling back to transformers backend.")
            return WhisperAudioTranscriber()

    if backend == "faster-whisper":
        if FasterWhisperAudioTranscriber is None:
            logger.warning(
                "faster-whisper is not installed. Falling back to transformers backend. "
                "Install with: poetry install --extras faster-whisper"
            )
            return WhisperAudioTranscriber()
        try:
            return FasterWhisperAudioTranscriber()
        except ImportError:
            logger.warning("faster-whisper not available. Falling back to transformers backend.")
            return WhisperAudioTranscriber()

    return WhisperAudioTranscriber()


def _ensure_ocr_available() -> bool:
    """Verify OCR backend dependencies when video analysis uses EasyOCR."""
    if OCR_ENGINE.lower() != "easyocr":
        return True
    try:
        import easyocr  # noqa: F401
        return True
    except ImportError:
        logger.error(
            "EasyOCR is required for video visual analysis. "
            "Install with: poetry install --extras scene-ocr"
        )
        return False


def create_video_pipeline(data_saver: DataSaver) -> VideoProcessingPipeline:
    """Build the keyframe-centric video processing pipeline."""
    scene_analyzer = PySceneDetectVideoSceneAnalyzer()
    ocr_extractor = create_ocr_extractor()
    keyframe_extractor = KeyframeExtractor(boundary_detector=HashSceneBoundaryDetector())
    return VideoProcessingPipeline(
        scene_analyzer,
        ocr_extractor,
        data_saver,
        keyframe_extractor=keyframe_extractor,
        max_workers=VIDEO_MAX_WORKERS,
        enable_parallel=VIDEO_ENABLE_PARALLEL,
    )


def run_pass_two(
    job_dir: str,
    extract_at: str,
    scene_output: str = "scene_analysis.json",
) -> int:
    """Two-pass enrichment: extract keyframes at agent-supplied timestamps."""
    job_dir = os.path.abspath(job_dir)
    if not os.path.isdir(job_dir):
        logger.error("Job directory does not exist: %s", job_dir)
        return 1

    data_saver = DataSaver(output_dir=job_dir)
    metadata = data_saver.load_job_metadata()
    if not metadata:
        logger.error(
            "job_metadata.json not found in %s. Re-run pass 1 with --enable_video_analysis.",
            job_dir,
        )
        return 1

    video_path = metadata.get("source_video_path")
    if not video_path or not os.path.isfile(video_path):
        logger.error(
            "source_video_path missing or not found in job_metadata.json: %r",
            video_path,
        )
        return 1

    if not _ensure_ocr_available():
        return 1

    phrase_timestamps = parse_timestamp_list(extract_at)
    if not phrase_timestamps:
        logger.error("No valid timestamps in --extract-at: %r", extract_at)
        return 1

    logger.info("Pass 2: extracting %d keyframes from %s", len(phrase_timestamps), video_path)
    video_pipeline = create_video_pipeline(data_saver)
    scene_results, _enrichment = video_pipeline.analyze(
        video_path,
        phrase_timestamps=phrase_timestamps,
        include_scene_boundary=False,
        include_periodic=False,
    )

    if scene_results:
        data_saver.save_scene_analysis(scene_output, scene_results)
    logger.info("Pass 2 visual enrichment complete in %s", job_dir)
    return 0


@timer
def main(
    echo_input,
    output_dir,
    transcription_output,
    enable_video_analysis: bool | None = None,
    scene_output="scene_analysis.json",
    subtitle_first: bool | None = None,
    transcriber_backend: str | None = None,
    job_dir: str | None = None,
    extract_at: str | None = None,
):
    """Main function to orchestrate the media processing pipeline."""
    if job_dir and extract_at:
        return run_pass_two(job_dir, extract_at, scene_output)

    if echo_input is None:
        logger.error("echo_input is required unless using --job-dir with --extract-at")
        return 1

    input_name = extract_input_name(echo_input)
    sanitized_input_name = sanitize_dir_name(input_name)
    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    dir_name = f"{timestamp}_{sanitized_input_name}"
    timestamped_output_dir = os.path.join(output_dir, dir_name)

    os.makedirs(timestamped_output_dir, exist_ok=True)
    logger.info(f"Output directory: {timestamped_output_dir}")

    if enable_video_analysis is None:
        enable_video_analysis = VIDEO_ANALYSIS_ENABLED

    if subtitle_first is None:
        subtitle_first = SUBTITLE_FIRST_ENABLED

    if enable_video_analysis and not _ensure_ocr_available():
        enable_video_analysis = False

    downloader = get_downloader(echo_input, timestamped_output_dir)
    # Download audio first to get path for language detection (reused by pipeline)
    audio_path = downloader.download(echo_input)
    transcriber = create_transcriber(transcriber_backend, audio_path=audio_path)
    diarizer = PyannoteDiarizer()
    aligner = SpeakerAligner()
    data_saver = DataSaver(output_dir=timestamped_output_dir)

    audio_pipeline = AudioProcessingPipeline(
        downloader, transcriber, diarizer, aligner, data_saver, subtitle_first=subtitle_first
    )

    video_pipeline = None
    video_path = None
    if enable_video_analysis:
        video_downloader = get_video_downloader(echo_input, timestamped_output_dir)
        if video_downloader:
            video_path = video_downloader.download(echo_input)
            if video_path:
                video_pipeline = create_video_pipeline(data_saver)
        elif os.path.isfile(echo_input) and echo_input.lower().endswith(
            (".mp4", ".webm", ".mkv", ".avi", ".mov")
        ):
            video_path = os.path.abspath(echo_input)
            video_pipeline = create_video_pipeline(data_saver)
        else:
            logger.warning("Video analysis enabled, but input is not a supported video source.")

    if video_path:
        data_saver.save_job_metadata(
            job_id=dir_name,
            echo_input=echo_input,
            source_video_path=video_path,
            video_analysis_enabled=bool(enable_video_analysis and video_pipeline),
        )

    orchestrator = MediaProcessingOrchestrator(
        audio_pipeline=audio_pipeline,
        video_pipeline=video_pipeline,
        enable_video_analysis=enable_video_analysis,
    )

    logger.info("Starting transcription process...")
    speaker_transcriptions, scene_results = orchestrator.process(echo_input, video_path, audio_path=audio_path)
    if speaker_transcriptions:
        source_info = get_source_info(echo_input)
        source_entry = ("", 0, 0, source_info)
        speaker_transcriptions_with_source = [source_entry] + speaker_transcriptions
        data_saver.save_data(transcription_output, speaker_transcriptions_with_source)
        csv_filename = os.path.splitext(transcription_output)[0] + ".csv"
        data_saver.save_transcriptions_to_csv(csv_filename, speaker_transcriptions_with_source)
        logger.info("Transcriptions complete")
    else:
        logger.warning("No transcriptions were generated.")

    if scene_results is not None:
        data_saver.save_scene_analysis(scene_output, scene_results)
        logger.info("Scene analysis complete")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EchoInStone Media Processing CLI")
    parser.add_argument(
        "echo_input",
        type=str,
        nargs="?",
        default=None,
        help="URL or path to media (optional in pass-2 mode with --job-dir)",
    )
    parser.add_argument("--output_dir", type=str, default="results", help="Directory to save output files")
    parser.add_argument(
        "--transcription_output",
        type=str,
        default="speaker_transcriptions.json",
        help="Filename for the transcription output",
    )
    video_group = parser.add_mutually_exclusive_group()
    video_group.add_argument(
        "--enable_video_analysis",
        action="store_true",
        help="Enable video keyframe extraction and scene-text OCR",
    )
    video_group.add_argument(
        "--disable_video_analysis",
        action="store_true",
        help="Disable video visual analysis",
    )
    parser.add_argument(
        "--scene_output",
        type=str,
        default="scene_analysis.json",
        help="Filename for the scene analysis output",
    )
    parser.add_argument(
        "--disable_subtitle_first",
        action="store_true",
        help="Disable subtitle-first extraction for YouTube videos",
    )
    parser.add_argument(
        "--transcriber_backend",
        type=str,
        default=None,
        choices=["auto", "transformers", "faster-whisper", "gigaam"],
        help="Transcription backend",
    )
    parser.add_argument(
        "--job-dir",
        type=str,
        default=None,
        help="Existing job output directory for pass-2 visual enrichment",
    )
    parser.add_argument(
        "--extract-at",
        type=str,
        default=None,
        help='Comma-separated timestamps for pass 2 (e.g. "5:00,12:30,45:00")',
    )

    args = parser.parse_args()

    if args.job_dir and not args.extract_at:
        parser.error("--extract-at is required when using --job-dir")
    if args.extract_at and not args.job_dir:
        parser.error("--job-dir is required when using --extract-at")

    if args.enable_video_analysis:
        enable_video_analysis = True
    elif args.disable_video_analysis:
        enable_video_analysis = False
    else:
        enable_video_analysis = None

    subtitle_first = None if not args.disable_subtitle_first else False

    exit_code = main(
        args.echo_input,
        args.output_dir,
        args.transcription_output,
        enable_video_analysis,
        args.scene_output,
        subtitle_first=subtitle_first,
        transcriber_backend=args.transcriber_backend,
        job_dir=args.job_dir,
        extract_at=args.extract_at,
    )
    sys.exit(exit_code or 0)
