"""Parse human-readable timestamps for --extract-at CLI values."""

from __future__ import annotations

import re


def parse_timestamp(value: str) -> float:
    """
    Parse mm:ss, hh:mm:ss, or decimal seconds into float seconds.

    Raises:
        ValueError: if the value cannot be parsed.
    """
    text = value.strip()
    if not text:
        raise ValueError("Empty timestamp")

    if re.fullmatch(r"\d+(\.\d+)?", text):
        return float(text)

    parts = text.split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    raise ValueError(f"Invalid timestamp format: {value!r}")


def parse_timestamp_list(raw: str) -> list[float]:
    """Parse comma-separated timestamps."""
    if not raw or not raw.strip():
        return []
    timestamps: list[float] = []
    for part in raw.split(","):
        part = part.strip()
        if part:
            timestamps.append(parse_timestamp(part))
    return sorted(set(timestamps))
