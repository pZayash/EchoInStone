#!/usr/bin/env python3
"""Wrap extract_transcript.py stdout into diarization/transcripts/*.txt layout."""
from __future__ import annotations

import sys


def main() -> None:
    meta: dict[str, str] = {}
    body: list[str] = []
    in_body = False
    for line in sys.stdin:
        line = line.rstrip("\n")
        if line == "---TRANSCRIPT---":
            in_body = True
            continue
        if in_body:
            body.append(line)
        elif "|" in line:
            key, value = line.split("|", 1)
            meta[key] = value.strip()

    vid = meta.get("VIDEO_ID", "unknown")
    title = meta.get("TITLE", "")
    channel = meta.get("CHANNEL", "")
    duration = meta.get("DURATION_SEC", "?")
    words = meta.get("WORDS", "?")
    sub = meta.get("SUB_LANG", "en-orig,en")
    text = "\n".join(body).strip()

    sys.stdout.write(
        f"# {title}\n"
        f"# Channel: {channel} | Duration: {duration}s | Words: {words}\n"
        f"# URL: https://www.youtube.com/watch?v={vid}\n"
        f"# Source: YouTube auto-captions ({sub})\n\n"
        f"---TRANSCRIPT---\n{text}\n"
    )


if __name__ == "__main__":
    main()
