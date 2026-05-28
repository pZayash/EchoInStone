#!/usr/bin/env python3
"""Download YouTube auto-captions and print a de-duplicated transcript on stdout."""
from __future__ import annotations

import argparse
import glob
import html
import os
import re
import subprocess
import sys


def video_id(url: str) -> str:
    match = re.search(
        r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([A-Za-z0-9_-]{11})",
        url,
    )
    if not match:
        raise SystemExit(f"Cannot parse YouTube video id from: {url}")
    return match.group(1)


def parse_vtt(path: str) -> list[str]:
    raw = open(path, encoding="utf-8").read()
    lines: list[str] = []
    for block in re.split(r"\n\n+", raw.strip()):
        if block.startswith("WEBVTT") or "Kind:" in block or "Language:" in block:
            continue
        parts: list[str] = []
        for line in block.strip().split("\n"):
            if "-->" in line or re.match(r"^\d+$", line):
                continue
            text = re.sub(r"<[^>]+>", "", line)
            text = html.unescape(text).strip()
            if text:
                parts.append(text)
        if parts:
            lines.append(" ".join(parts))
    return lines


def merge_rolling(lines: list[str]) -> str:
    full = ""
    for line in lines:
        if not full:
            full = line
            continue
        overlap = 0
        limit = min(len(full), len(line))
        for i in range(limit, 0, -1):
            if full[-i:] == line[:i]:
                overlap = i
                break
        full += line[overlap:]
    return full


def to_paragraphs(text: str, words_per_para: int = 75) -> str:
    words = text.split()
    paragraphs: list[str] = []
    buffer: list[str] = []
    word_count = 0
    for word in words:
        buffer.append(word)
        word_count += 1
        if word.endswith((".", "?", "!")) and word_count >= words_per_para:
            paragraphs.append(" ".join(buffer))
            buffer, word_count = [], 0
    if buffer:
        paragraphs.append(" ".join(buffer))
    return "\n\n".join(paragraphs)


def download_vtt(url: str, vid: str, sub_langs: str) -> str:
    subprocess.run(
        [
            "yt-dlp",
            "--no-update",
            "--write-auto-subs",
            "--sub-lang",
            sub_langs,
            "--sub-format",
            "vtt",
            "--skip-download",
            "-o",
            vid,
            url,
            "-q",
        ],
        check=True,
        stderr=subprocess.DEVNULL,
    )
    first_lang = sub_langs.split(",")[0]
    for candidate in (f"{vid}.{first_lang}.vtt", f"{vid}.vtt"):
        if os.path.isfile(candidate):
            return candidate
    hits = glob.glob(f"{vid}*.vtt")
    if not hits:
        print("NO_SUBTITLES|true", flush=True)
        raise SystemExit(2)
    return hits[0]


def fetch_meta(url: str) -> tuple[str, str, str]:
    output = subprocess.check_output(
        [
            "yt-dlp",
            "--no-update",
            "--print",
            "%(title)s|%(channel)s|%(duration)s",
            url,
        ],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()
    title, channel, duration = (output.split("|") + ["", "", ""])[:3]
    return title, channel, duration


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument(
        "--sub-lang",
        default="en-orig,en",
        help="yt-dlp subtitle languages (comma-separated)",
    )
    parser.add_argument(
        "--save-format",
        action="store_true",
        help="Emit diarization/transcripts/*.txt layout (for host redirect)",
    )
    args = parser.parse_args()
    vid = video_id(args.url)

    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "yt-dlp"], check=False)

    title, channel, duration = fetch_meta(args.url)
    vtt_path = download_vtt(args.url, vid, args.sub_lang)
    text = merge_rolling(parse_vtt(vtt_path))
    word_count = len(text.split())

    body = to_paragraphs(text)
    if args.save_format:
        print(f"# {title}")
        print(f"# Channel: {channel} | Duration: {duration}s | Words: {word_count}")
        print(f"# URL: https://www.youtube.com/watch?v={vid}")
        print(f"# Source: YouTube auto-captions ({args.sub_lang})")
        print()
        print("---TRANSCRIPT---")
        print(body)
        return

    print(f"VIDEO_ID|{vid}")
    print(f"TITLE|{title}")
    print(f"CHANNEL|{channel}")
    print(f"DURATION_SEC|{duration}")
    print(f"SUB_LANG|{args.sub_lang}")
    print(f"WORDS|{word_count}")
    print("---TRANSCRIPT---")
    print(body)


if __name__ == "__main__":
    main()
