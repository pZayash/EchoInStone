#!/usr/bin/env python3
"""Convert EchoInStone speaker_transcriptions.json to plain text."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def export(json_path: Path, out_path: Path, video_url: str = "") -> int:
    rows = json.loads(json_path.read_text(encoding="utf-8"))
    paragraphs: list[str] = []
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 4:
            continue
        speaker, start, end, text = row[0], row[1], row[2], row[3]
        if start == 0 and end == 0:
            continue
        line = str(text).strip()
        if not line:
            continue
        if speaker:
            line = f"[{speaker}] {line}"
        paragraphs.append(line)

    header = [
        f"# Source: EchoInStone (Whisper + pyannote diarization)",
    ]
    if video_url:
        header.append(f"# URL: {video_url}")
    header.append(f"# Input: {json_path}")
    header.append("")
    header.append("---TRANSCRIPT---")
    header.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(header) + "\n\n".join(paragraphs) + "\n", encoding="utf-8")
    return len(paragraphs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", type=Path)
    parser.add_argument("out_path", type=Path)
    parser.add_argument("--url", default="")
    args = parser.parse_args()
    count = export(args.json_path, args.out_path, args.url)
    print(f"SEGMENTS|{count}")
    print(f"OUTPUT|{args.out_path}")


if __name__ == "__main__":
    main()
