"""Keyframe records and manifest persistence for visual enrichment."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


TRIGGER_SCENE_BOUNDARY = "scene_boundary"
TRIGGER_PERIODIC_FALLBACK = "periodic_fallback"
TRIGGER_PHRASE_TIMESTAMP = "phrase_timestamp"

TRIGGER_PRIORITY = {
    TRIGGER_PHRASE_TIMESTAMP: 0,
    TRIGGER_SCENE_BOUNDARY: 1,
    TRIGGER_PERIODIC_FALLBACK: 2,
}


@dataclass
class KeyframeRecord:
    """A captured keyframe with optional OCR results."""

    id: str
    timestamp_seconds: float
    trigger: str
    image_path: Optional[str] = None
    ocr_text: str = ""
    ocr_confidence: float = 0.0
    ocr_engine: str = "none"
    created_at: str = ""
    triggers: List[str] = field(default_factory=list)

    def to_enrichment_dict(self) -> dict:
        """Shape for visual_enrichment.json entries."""
        return {
            "id": self.id,
            "timestamp_seconds": self.timestamp_seconds,
            "trigger": self.trigger,
            "triggers": self.triggers or [self.trigger],
            "image_path": self.image_path,
            "extracted_text": self.ocr_text,
            "ocr_confidence": self.ocr_confidence,
            "ocr_engine": self.ocr_engine,
            "created_at": self.created_at,
        }

    def to_manifest_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp_seconds": self.timestamp_seconds,
            "trigger": self.trigger,
            "triggers": self.triggers or [self.trigger],
            "image_path": self.image_path,
            "ocr_text": self.ocr_text,
            "ocr_confidence": self.ocr_confidence,
            "ocr_engine": self.ocr_engine,
            "created_at": self.created_at,
        }


@dataclass
class TriggerEvent:
    """A pending keyframe extraction at a specific time."""

    timestamp_seconds: float
    trigger: str


def new_keyframe_id() -> str:
    return uuid.uuid4().hex[:8]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def merge_trigger_events(
    events: List[TriggerEvent],
    dedup_seconds: float,
    max_count: int,
) -> List[TriggerEvent]:
    """Deduplicate triggers by time window and cap count by priority."""
    if not events:
        return []

    sorted_events = sorted(events, key=lambda e: e.timestamp_seconds)
    merged: List[TriggerEvent] = []

    for event in sorted_events:
        if merged and abs(event.timestamp_seconds - merged[-1].timestamp_seconds) <= dedup_seconds:
            existing = merged[-1]
            combined = sorted(
                {existing.trigger, event.trigger},
                key=lambda t: TRIGGER_PRIORITY.get(t, 99),
            )
            primary = combined[0]
            merged[-1] = TriggerEvent(timestamp_seconds=existing.timestamp_seconds, trigger=primary)
            continue
        merged.append(event)

    if len(merged) <= max_count:
        return merged

    ranked = sorted(
        merged,
        key=lambda e: (TRIGGER_PRIORITY.get(e.trigger, 99), e.timestamp_seconds),
    )
    kept = ranked[:max_count]
    return sorted(kept, key=lambda e: e.timestamp_seconds)


class KeyframeManifest:
    """Read/write keyframes/manifest.json with merge support for pass 2."""

    def __init__(self, manifest_path: str):
        self.manifest_path = manifest_path
        self.keyframes: List[KeyframeRecord] = []
        self._load()

    def _load(self) -> None:
        if not os.path.isfile(self.manifest_path):
            return
        try:
            with open(self.manifest_path, encoding="utf-8") as handle:
                payload = json.load(handle)
            for entry in payload.get("keyframes", []):
                self.keyframes.append(
                    KeyframeRecord(
                        id=entry.get("id", new_keyframe_id()),
                        timestamp_seconds=float(entry["timestamp_seconds"]),
                        trigger=entry.get("trigger", TRIGGER_SCENE_BOUNDARY),
                        image_path=entry.get("image_path"),
                        ocr_text=entry.get("ocr_text", ""),
                        ocr_confidence=float(entry.get("ocr_confidence", 0.0)),
                        ocr_engine=entry.get("ocr_engine", "none"),
                        created_at=entry.get("created_at", ""),
                        triggers=entry.get("triggers") or [entry.get("trigger", "")],
                    )
                )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            self.keyframes = []

    def existing_timestamps(self) -> set[tuple[float, str]]:
        return {
            (round(k.timestamp_seconds, 2), k.trigger) for k in self.keyframes
        }

    def append(self, record: KeyframeRecord) -> None:
        key = (round(record.timestamp_seconds, 2), record.trigger)
        if key in self.existing_timestamps():
            return
        self.keyframes.append(record)

    def merge_records(self, records: List[KeyframeRecord]) -> None:
        for record in records:
            self.append(record)
        self.keyframes.sort(key=lambda k: k.timestamp_seconds)

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
        payload = {
            "keyframes": [k.to_manifest_dict() for k in self.keyframes],
        }
        tmp_path = self.manifest_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.manifest_path)

    def to_enrichment_entries(self) -> List[dict]:
        return [k.to_enrichment_dict() for k in self.keyframes]
