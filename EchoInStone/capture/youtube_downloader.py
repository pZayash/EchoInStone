import yt_dlp
import os
import re
import logging
from typing import Optional
from pydub import AudioSegment
from ..capture import DownloaderInterface
from ..config import SUBTITLE_PREFERRED_LANGUAGES, SUBTITLE_PREFER_MANUAL

logger = logging.getLogger(__name__)

class YouTubeDownloader(DownloaderInterface):
    def __init__(self, output_dir='data/videos'):
        """
        Initializes the YouTubeDownloader with a specified output directory.

        Args:
            output_dir (str): The directory where downloaded files will be saved.
        """
        self.output_dir = output_dir

    def download(self, url: str) -> str:
        """
        Downloads audio from a YouTube URL and converts it to WAV format.

        Args:
            url (str): YouTube URL to download audio from.

        Returns:
            str: Path to the saved WAV file if the download and conversion were successful, None otherwise.
        """
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.output_dir, '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'js_runtimes': {'node': {}},
                'remote_components': ['ejs:github']
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)

            # Convert the file to WAV
            audio = AudioSegment.from_file(downloaded_file)
            
            # Clean up the file name for the wav file
            title = info.get('title', 'audio')
            safe_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '_')
            wav_file = os.path.join(self.output_dir, safe_title + '.wav')
            
            audio.export(wav_file, format="wav")
            
            # Remove the original downloaded file
            if os.path.exists(downloaded_file) and downloaded_file != wav_file:
                os.remove(downloaded_file)

            logger.info(f"Audio downloaded and converted to {wav_file}")
            return wav_file
        except Exception as e:
            logger.error(f"Error during download: {e}")
            return None

    def fetch_subtitles(self, url: str) -> Optional[tuple[str, list]]:
        """
        Extracts native subtitles from a YouTube video without downloading audio.

        Args:
            url (str): YouTube URL to extract subtitles from.

        Returns:
            Optional[tuple[str, list]]: Tuple of (language_code, subtitle_entries) where
                subtitle_entries is a list of {"timestamp": (start, end), "text": str} dicts,
                or None if no suitable subtitles are found.
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitlesformat': 'vtt',
                'js_runtimes': {'node': {}},
                'remote_components': ['ejs:github'],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            manual_subs = info.get('subtitles') or {}
            auto_subs = info.get('automatic_captions') or {}

            selected = self._select_subtitles(manual_subs, auto_subs)
            if selected is None:
                logger.info("No subtitles matched preferred languages.")
                return None

            lang, sub_info, is_auto = selected
            sub_url = self._get_subtitle_url(sub_info)
            if sub_url is None:
                logger.warning(f"No downloadable subtitle URL found for language '{lang}'.")
                return None

            # Download subtitle content
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                subtitle_content = ydl.urlopen(sub_url).read().decode('utf-8')

            # Detect format and parse
            if sub_url.endswith('.srt') or 'fmt=srt' in sub_url:
                entries = self._parse_srt(subtitle_content)
            else:
                entries = self._parse_vtt(subtitle_content)

            if not entries:
                logger.warning("Subtitle parsing returned no entries.")
                return None

            source_type = "auto-generated" if is_auto else "manual"
            logger.info(f"Extracted {len(entries)} subtitle entries ({source_type}, lang={lang}).")
            if is_auto:
                logger.warning("Using auto-generated subtitles (quality may vary).")

            return lang, entries

        except Exception as e:
            logger.error(f"Error extracting subtitles: {e}")
            return None

    def _select_subtitles(
        self,
        manual_subs: dict,
        auto_subs: dict,
    ) -> Optional[tuple[str, list, bool]]:
        """
        Selects the best subtitle track based on language priority and manual preference.

        Returns:
            Optional[tuple[str, list, bool]]: (language, sub_info_list, is_auto) or None.
        """
        for lang in SUBTITLE_PREFERRED_LANGUAGES:
            if SUBTITLE_PREFER_MANUAL and lang in manual_subs:
                return lang, manual_subs[lang], False
            if lang in auto_subs:
                return lang, auto_subs[lang], True
            # If not preferring manual, still check manual as fallback
            if not SUBTITLE_PREFER_MANUAL and lang in manual_subs:
                return lang, manual_subs[lang], False
        return None

    @staticmethod
    def _get_subtitle_url(sub_info_list: list) -> Optional[str]:
        """Extracts the best subtitle download URL from yt-dlp subtitle info."""
        # Prefer vtt format
        for entry in sub_info_list:
            if entry.get('ext') == 'vtt':
                return entry.get('url')
        # Fallback to srt
        for entry in sub_info_list:
            if entry.get('ext') == 'srt':
                return entry.get('url')
        # Fallback to any available
        if sub_info_list:
            return sub_info_list[0].get('url')
        return None

    @staticmethod
    def _parse_vtt(content: str) -> list[dict]:
        """
        Parses VTT subtitle content with YouTube rolling-append deduplication.

        Returns:
            list[dict]: List of {"timestamp": (start_seconds, end_seconds), "text": str}.
        """
        lines = content.strip().split('\n')
        entries = []
        timestamp_pattern = re.compile(
            r'(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})'
        )

        i = 0
        while i < len(lines):
            match = timestamp_pattern.search(lines[i])
            if match:
                start = (int(match.group(1)) * 3600 + int(match.group(2)) * 60 +
                         int(match.group(3)) + int(match.group(4)) / 1000.0)
                end = (int(match.group(5)) * 3600 + int(match.group(6)) * 60 +
                       int(match.group(7)) + int(match.group(8)) / 1000.0)
                i += 1
                text_lines = []
                while i < len(lines) and lines[i].strip() and not timestamp_pattern.search(lines[i]):
                    # Strip VTT positioning tags like <c>, </c>, etc.
                    cleaned = re.sub(r'<[^>]+>', '', lines[i]).strip()
                    if cleaned:
                        text_lines.append(cleaned)
                    i += 1
                text = ' '.join(text_lines).strip()
                if text:
                    entries.append({"timestamp": (start, end), "text": text})
            else:
                i += 1

        # Deduplicate rolling-append: if one entry's text is a prefix of the next, skip it
        if not entries:
            return entries

        deduped = []
        for j in range(len(entries) - 1):
            current_text = entries[j]["text"]
            next_text = entries[j + 1]["text"]
            if not next_text.startswith(current_text):
                deduped.append(entries[j])
        deduped.append(entries[-1])

        return deduped

    @staticmethod
    def _parse_srt(content: str) -> list[dict]:
        """
        Parses SRT subtitle content with timestamp normalization to float seconds.

        Returns:
            list[dict]: List of {"timestamp": (start_seconds, end_seconds), "text": str}.
        """
        entries = []
        blocks = re.split(r'\n\s*\n', content.strip())
        timestamp_pattern = re.compile(
            r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})'
        )

        for block in blocks:
            lines = block.strip().split('\n')
            for idx, line in enumerate(lines):
                match = timestamp_pattern.search(line)
                if match:
                    start = (int(match.group(1)) * 3600 + int(match.group(2)) * 60 +
                             int(match.group(3)) + int(match.group(4)) / 1000.0)
                    end = (int(match.group(5)) * 3600 + int(match.group(6)) * 60 +
                           int(match.group(7)) + int(match.group(8)) / 1000.0)
                    text = ' '.join(lines[idx + 1:]).strip()
                    text = re.sub(r'<[^>]+>', '', text)
                    if text:
                        entries.append({"timestamp": (start, end), "text": text})
                    break

        return entries

    def validate_url(self, url: str) -> bool:
        """
        Validates if a URL is a valid YouTube URL.

        Args:
            url (str): URL to validate.

        Returns:
            bool: True if the URL is a valid YouTube URL, False otherwise.
        """
        try:
            ydl_opts = {
                'quiet': True, 
                'no_warnings': True,
                'js_runtimes': {'node': {}},
                'remote_components': ['ejs:github']
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=False)
            return True
        except Exception:
            logger.warning(f"Invalid YouTube URL: {url}")
            return False
