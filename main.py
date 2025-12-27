import argparse
import os
import re
from datetime import datetime
from urllib.parse import urlparse
from EchoInStone.utils import configure_logging
import logging

from pytubefix import YouTube
from EchoInStone.capture.downloader_factory import get_downloader
from EchoInStone.processing import AudioProcessingOrchestrator, WhisperAudioTranscriber, PyannoteDiarizer, SpeakerAligner
from EchoInStone.utils import DataSaver
from EchoInStone.utils import timer, log_time

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
            # Get video title from YouTube
            yt = YouTube(echo_input)
            video_title = yt.title
            if video_title:
                # Clean up the title and use it
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


# Youtube = 'https://www.youtube.com/watch?v=ipXG9iQq-Tw'
# Podcast = 'https://radiofrance-podcast.net/podcast09/rss_13957.xml'

# Test Youtube video = 'https://www.youtube.com/watch?v=plZRCMx_Jd8'
# Test Podcast = 'https://radiofrance-podcast.net/podcast09/rss_13957.xml'
# Test MP3 File = 'https://media.radiofrance-podcast.net/podcast09/25425-13.02.2025-ITEMA_24028677-2025C53905E0006-NET_MFC_D378B90D-D570-44E9-AB5A-F0CC63B05A14-21.mp3'


@timer
def main(echo_input, output_dir, transcription_output):
    """
    Main function to orchestrate the audio processing pipeline.
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
    
    # Initialize components with timestamped output directory
    downloader = get_downloader(echo_input, timestamped_output_dir)
    transcriber = WhisperAudioTranscriber()
    diarizer = PyannoteDiarizer()
    aligner = SpeakerAligner()
    data_saver = DataSaver(output_dir=timestamped_output_dir)

    # Create an instance of AudioProcessingOrchestrator
    orchestrator = AudioProcessingOrchestrator(downloader, transcriber, diarizer, aligner, data_saver)

    # Process the input URL
    logger.info("Starting transcription process...")
    speaker_transcriptions = orchestrator.extract_and_transcribe(echo_input)
    if speaker_transcriptions:
        # Save the results to JSON file
        data_saver.save_data(transcription_output, speaker_transcriptions)

        # Save the results to CSV file
        csv_filename = os.path.splitext(transcription_output)[0] + ".csv"
        data_saver.save_transcriptions_to_csv(csv_filename, speaker_transcriptions)

        logger.info(f"Transcriptions complete")
        
    else:
        logger.warning("No transcriptions were generated.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EchoInStone Audio Processing CLI")
    parser.add_argument("echo_input", type=str, help="URL of the audio input (YouTube, podcast, or direct audio file)")
    parser.add_argument("--output_dir", type=str, default="results", help="Directory to save the output files")
    parser.add_argument("--transcription_output", type=str, default="speaker_transcriptions.json", help="Filename for the transcription output")

    args = parser.parse_args()

    main(args.echo_input, args.output_dir, args.transcription_output)