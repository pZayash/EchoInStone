import argparse
import os
import re
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
    PyannoteDiarizer,
    SpeakerAligner,
    PySceneDetectVideoSceneAnalyzer,
    TesseractOCRTextExtractor,
)
from EchoInStone.utils import DataSaver
from EchoInStone.utils import timer, log_time
from EchoInStone.config import (
    VIDEO_ANALYSIS_ENABLED,
    VIDEO_ENABLE_PARALLEL,
    VIDEO_FRAME_SAMPLING_SECONDS,
    VIDEO_MAX_SCENE_SAMPLES,
    VIDEO_MAX_WORKERS,
    VIDEO_PROCESSING_PROFILE,
    VIDEO_PROFILE_SETTINGS,
    SUBTITLE_FIRST_ENABLED,
    TRANSCRIBER_BACKEND,
)

# Configure logging
configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


def extract_input_name(echo_input: str) -> str:
    """
    Extracts a safe filename from the input (URL, local file path, etc.)
    to use in the output directory name.
    
    Args:
        echo_input (str): Input URL or file path
        
    Returns:
        str: Safe filename for use in directory name
    """
    # Check if it's a local file
    if os.path.isfile(echo_input):
        base_name = os.path.basename(echo_input)
        name_without_ext = os.path.splitext(base_name)[0]
        return name_without_ext
    
    # Parse URL
    parsed_url = urlparse(echo_input)
    
    # Handle YouTube URLs
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
        
        # Fallback: use video ID if title fetch failed
        video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', echo_input)
        if video_id_match:
            return f"youtube_{video_id_match.group(1)}"
        return "youtube_video"
    
    # Handle podcast RSS feeds
    if echo_input.endswith(".xml"):
        # Extract podcast name from URL or use a default
        path_parts = [p for p in parsed_url.path.split('/') if p]
        if path_parts:
            return os.path.splitext(path_parts[-1])[0]
        return "podcast"
    
    # For direct file URLs, extract filename from path
    if parsed_url.path:
        filename = os.path.basename(parsed_url.path)
        if filename:
            name_without_ext = os.path.splitext(filename)[0]
            if name_without_ext:
                return name_without_ext
    
    # Fallback: use domain name or a default
    if parsed_url.netloc:
        domain = parsed_url.netloc.replace('.', '_')
        return domain[:50]  # Limit length
    
    # Last resort: use a sanitized version of the input
    safe_name = re.sub(r'[^\w\s-]', '', echo_input).replace(' ', '_')[:50]
    return safe_name if safe_name else "input"


def sanitize_dir_name(name: str) -> str:
    """
    Sanitizes a string to be safe for use as a directory name.
    
    Args:
        name (str): String to sanitize
        
    Returns:
        str: Sanitized string safe for directory names
    """
    # Remove or replace invalid characters for directory names
    # Windows: < > : " | ? * \
    # Also remove leading/trailing spaces and dots
    sanitized = re.sub(r'[<>:"|?*\\]', '', name)
    sanitized = sanitized.strip(' .')
    # Replace multiple spaces/underscores with single underscore
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    # Limit length to avoid path issues
    return sanitized[:100] if sanitized else "input"


def get_source_info(echo_input: str) -> str:
    """
    Gets the source information (YouTube URL or filename) for transcription output.
    
    Args:
        echo_input (str): Input URL or file path
        
    Returns:
        str: YouTube URL if input is YouTube, otherwise the filename or URL
    """
    # Check if it's a YouTube URL
    if "youtube.com" in echo_input or "youtu.be" in echo_input:
        return echo_input
    
    # Check if it's a local file
    if os.path.isfile(echo_input):
        return os.path.basename(echo_input)
    
    # For URLs or other inputs, return as is
    return echo_input


# Youtube = 'https://www.youtube.com/watch?v=ipXG9iQq-Tw'
# Podcast = 'https://radiofrance-podcast.net/podcast09/rss_13957.xml'

# Test Youtube video = 'https://www.youtube.com/watch?v=plZRCMx_Jd8'
# Test Podcast = 'https://radiofrance-podcast.net/podcast09/rss_13957.xml'
# Test MP3 File = 'https://media.radiofrance-podcast.net/podcast09/25425-13.02.2025-ITEMA_24028677-2025C53905E0006-NET_MFC_D378B90D-D570-44E9-AB5A-F0CC63B05A14-21.mp3'


def create_transcriber(backend: str | None = None):
    """Create a transcriber instance based on backend selection.

    Args:
        backend: "auto", "transformers", "faster-whisper", or None (uses config default).

    Returns:
        An AudioTranscriberInterface implementation.
    """
    import torch

    if backend is None:
        backend = TRANSCRIBER_BACKEND

    if backend == "auto":
        if torch.xpu.is_available():
            backend = "transformers"
            logger.info("Auto-selected 'transformers' backend (Intel XPU detected)")
        else:
            backend = "faster-whisper"
            logger.info("Auto-selected 'faster-whisper' backend")

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

    # Default: transformers
    return WhisperAudioTranscriber()


@timer
def main(
    echo_input,
    output_dir,
    transcription_output,
    enable_video_analysis: bool | None = None,
    scene_output="scene_analysis.json",
    subtitle_first: bool | None = None,
    transcriber_backend: str | None = None,
):
    """
    Main function to orchestrate the media processing pipeline.
    """
    # Extract input name and create timestamped subdirectory
    input_name = extract_input_name(echo_input)
    sanitized_input_name = sanitize_dir_name(input_name)
    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    
    # Create directory name: yyMMdd_hhmm_inputname
    dir_name = f"{timestamp}_{sanitized_input_name}"
    timestamped_output_dir = os.path.join(output_dir, dir_name)
    
    # Ensure the timestamped directory exists
    os.makedirs(timestamped_output_dir, exist_ok=True)
    logger.info(f"Output directory: {timestamped_output_dir}")
    
    # Apply default configuration for video analysis if not explicitly set
    if enable_video_analysis is None:
        enable_video_analysis = VIDEO_ANALYSIS_ENABLED

    # Apply default configuration for subtitle-first if not explicitly set
    if subtitle_first is None:
        subtitle_first = SUBTITLE_FIRST_ENABLED

    # Initialize components with timestamped output directory
    downloader = get_downloader(echo_input, timestamped_output_dir)
    transcriber = create_transcriber(transcriber_backend)
    diarizer = PyannoteDiarizer()
    aligner = SpeakerAligner()
    data_saver = DataSaver(output_dir=timestamped_output_dir)

    audio_pipeline = AudioProcessingPipeline(downloader, transcriber, diarizer, aligner, data_saver, subtitle_first=subtitle_first)

    video_pipeline = None
    video_path = None
    if enable_video_analysis:
        video_downloader = get_video_downloader(echo_input, timestamped_output_dir)
        if video_downloader:
            video_path = video_downloader.download(echo_input)
            if video_path:
                profile_settings = VIDEO_PROFILE_SETTINGS.get(VIDEO_PROCESSING_PROFILE, {})
                scene_analyzer = PySceneDetectVideoSceneAnalyzer()
                ocr_extractor = TesseractOCRTextExtractor()
                video_pipeline = VideoProcessingPipeline(
                    scene_analyzer,
                    ocr_extractor,
                    data_saver,
                    frame_sampling_seconds=profile_settings.get(
                        "frame_sampling_seconds", VIDEO_FRAME_SAMPLING_SECONDS
                    ),
                    max_workers=profile_settings.get("max_workers", VIDEO_MAX_WORKERS),
                    enable_parallel=profile_settings.get("enable_parallel", VIDEO_ENABLE_PARALLEL),
                    max_scene_samples=profile_settings.get("max_scene_samples", VIDEO_MAX_SCENE_SAMPLES),
                )
        else:
            logger.warning("Video analysis enabled, but input is not a supported video source.")

    orchestrator = MediaProcessingOrchestrator(
        audio_pipeline=audio_pipeline,
        video_pipeline=video_pipeline,
        enable_video_analysis=enable_video_analysis,
    )

    # Process the input URL
    logger.info("Starting transcription process...")
    speaker_transcriptions, scene_results = orchestrator.process(echo_input, video_path)
    if speaker_transcriptions:
        # Get source information (YouTube URL or filename)
        source_info = get_source_info(echo_input)
        
        # Add source information at the beginning of transcriptions
        # Format: (speaker, start, end, text) with start=0, end=0
        source_entry = ("", 0, 0, source_info)
        speaker_transcriptions_with_source = [source_entry] + speaker_transcriptions
        
        # Save the results to JSON file
        data_saver.save_data(transcription_output, speaker_transcriptions_with_source)

        # Save the results to CSV file
        csv_filename = os.path.splitext(transcription_output)[0] + ".csv"
        data_saver.save_transcriptions_to_csv(csv_filename, speaker_transcriptions_with_source)

        logger.info(f"Transcriptions complete")
        
    else:
        logger.warning("No transcriptions were generated.")

    if scene_results is not None:
        data_saver.save_scene_analysis(scene_output, scene_results)
        logger.info("Scene analysis complete")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EchoInStone Media Processing CLI")
    parser.add_argument("echo_input", type=str, help="URL of the audio input (YouTube, podcast, or direct audio file)")
    parser.add_argument("--output_dir", type=str, default="results", help="Directory to save the output files")
    parser.add_argument("--transcription_output", type=str, default="speaker_transcriptions.json", help="Filename for the transcription output")
    video_group = parser.add_mutually_exclusive_group()
    video_group.add_argument("--enable_video_analysis", action="store_true", help="Enable video scene analysis if input is video")
    video_group.add_argument("--disable_video_analysis", action="store_true", help="Disable video scene analysis")
    parser.add_argument("--scene_output", type=str, default="scene_analysis.json", help="Filename for the scene analysis output")
    parser.add_argument("--disable_subtitle_first", action="store_true", help="Disable subtitle-first extraction for YouTube videos")
    parser.add_argument("--transcriber_backend", type=str, default=None, choices=["auto", "transformers", "faster-whisper"], help="Transcription backend: auto, transformers, or faster-whisper")

    args = parser.parse_args()
    if args.enable_video_analysis:
        enable_video_analysis = True
    elif args.disable_video_analysis:
        enable_video_analysis = False
    else:
        enable_video_analysis = None

    subtitle_first = None if not args.disable_subtitle_first else False

    main(
        args.echo_input,
        args.output_dir,
        args.transcription_output,
        enable_video_analysis,
        args.scene_output,
        subtitle_first=subtitle_first,
        transcriber_backend=args.transcriber_backend,
    )