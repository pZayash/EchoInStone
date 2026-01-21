import os
import logging
import shutil
import requests
from urllib.parse import urlparse
from pytubefix import YouTube

from .downloader_interface import DownloaderInterface

logger = logging.getLogger(__name__)


class VideoDownloader(DownloaderInterface):
    def __init__(self, output_dir='data/videos'):
        self.output_dir = output_dir

    def download(self, source: str) -> str:
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            parsed_url = urlparse(source)
            is_url = bool(parsed_url.netloc)

            if "youtube.com" in source or "youtu.be" in source:
                yt = YouTube(source)
                stream = yt.streams.filter(progressive=True, file_extension="mp4").first()
                if not stream:
                    raise RuntimeError("No progressive MP4 stream available for download.")
                video_file = stream.download(output_path=self.output_dir)
                logger.info(f"Video downloaded to {video_file}")
                return os.path.abspath(video_file)

            if is_url:
                logger.info(f"Downloading video from URL: {source}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(source, stream=True, headers=headers)
                response.raise_for_status()
                file_name = os.path.basename(parsed_url.path) or "downloaded_video"
                destination_path = os.path.join(self.output_dir, file_name)
                with open(destination_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Video downloaded to {destination_path}")
                return os.path.abspath(destination_path)

            # Local file copy
            logger.info(f"Copying local video file: {source}")
            file_name = os.path.basename(source)
            destination_path = os.path.join(self.output_dir, file_name)
            shutil.copy2(source, destination_path)
            return os.path.abspath(destination_path)
        except Exception as exc:
            logger.error(f"Error during video download/copy: {exc}")
            return None

    def validate_url(self, source: str) -> bool:
        try:
            if "youtube.com" in source or "youtu.be" in source:
                YouTube(source)
                return True

            parsed_url = urlparse(source)
            is_url = bool(parsed_url.netloc)
            if is_url:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.head(source, timeout=10, headers=headers)
                return response.status_code == 200

            return os.path.isfile(source)
        except Exception:
            return False
