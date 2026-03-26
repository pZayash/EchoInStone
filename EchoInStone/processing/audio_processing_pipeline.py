from ..capture import DownloaderInterface
from ..capture.youtube_downloader import YouTubeDownloader
from .audio_transcriber_interface import AudioTranscriberInterface
from .diarizer_interface import DiarizerInterface
from ..utils import DataSaver
from .aligner_interface import AlignerInterface

import logging

logger = logging.getLogger(__name__)


class AudioProcessingPipeline:
    def __init__(self, downloader: DownloaderInterface,
                 transcriber: AudioTranscriberInterface,
                 diarizer: DiarizerInterface,
                 aligner: AlignerInterface,
                 saver: DataSaver,
                 subtitle_first: bool = False):
        self.downloader = downloader
        self.transcriber = transcriber
        self.diarizer = diarizer
        self.aligner = aligner
        self.saver = saver
        self.subtitle_first = subtitle_first

    def process(self, echo_input: str):
        """
        Runs the audio processing pipeline: download, transcribe, diarize, align.
        When subtitle_first is enabled and downloader is YouTubeDownloader,
        attempts to extract subtitles before downloading audio.
        """
        # Subtitle-first fast path
        if self.subtitle_first and isinstance(self.downloader, YouTubeDownloader):
            try:
                result = self.downloader.fetch_subtitles(echo_input)
                if result is not None:
                    lang, subtitle_entries = result
                    logger.info(f"Using subtitle-first path (lang={lang}, {len(subtitle_entries)} entries).")

                    # Convert subtitle entries to speaker transcription format
                    # Format: list of (speaker, start, end, text)
                    transcriptions = [
                        ("", entry["timestamp"][0], entry["timestamp"][1], entry["text"])
                        for entry in subtitle_entries
                    ]
                    return transcriptions
                else:
                    logger.info("No subtitles found, falling back to standard pipeline.")
            except Exception as e:
                logger.warning(f"Subtitle extraction failed, falling back to standard pipeline: {e}")

        # Standard pipeline: download, transcribe, diarize, align
        logger.debug("Downloading audio...")
        audio_path = self.downloader.download(echo_input)
        if audio_path:
            logger.debug("Transcribing downloaded audio...")
            transcription, timestamps = self.transcriber.transcribe(audio_path)
            logger.debug("Diarizing downloaded audio...")
            diarization = self.diarizer.diarize(audio_path)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Writing debug files.")
                self.saver.save_data("audio_transcription.txt", transcription)
                self.saver.save_data("audio_timestamps.json", timestamps)
                self.saver.save_data("audio_diarization.txt", str(diarization))

            return self.aligner.align(transcription, timestamps, diarization)
        return None
