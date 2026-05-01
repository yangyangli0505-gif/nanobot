"""Snapshot persistence and change detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .models import IntelligenceEvent
except ImportError:
    from models import IntelligenceEvent


DEFAULT_STATE_DIR = Path(__file__).with_name("state")
DEFAULT_SNAPSHOT_PATH = DEFAULT_STATE_DIR / "latest_snapshot.json"


def save_snapshot(events: list[IntelligenceEvent], path: str | Path | None = None) -> Path:
    target = Path(path) if path else DEFAULT_SNAPSHOT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = [event.to_dict() for event in events]
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def load_snapshot(path: str | Path | None = None) -> list[dict[str, Any]]:
    target = Path(path) if path else DEFAULT_SNAPSHOT_PATH
    if not target.exists():
        return []
    return json.loads(target.read_text(encoding="utf-8"))


def diff_events(current_events: list[IntelligenceEvent], previous_snapshot: list[dict[str, Any]]) -> dict[str, list[IntelligenceEvent]]:
    prev_by_id = {item.get("event_id"): item for item in previous_snapshot if item.get("event_id")}
    current_ids = {event.ensure_id() for event in current_events}

    added: list[IntelligenceEvent] = []
    repeated: list[IntelligenceEvent] = []
    escalated: list[IntelligenceEvent] = []

    for event in current_events:
        eid = event.ensure_id()
        prev = prev_by_id.get(eid)
        if prev is None:
            added.append(event)
            continue

        repeated.append(event)
        prev_score = float(prev.get("signal_score", 0.0))
        if event.signal_score - prev_score >= 0.20:
            escalated.append(event)

    disappeared_ids = set(prev_by_id.keys()) - current_ids
    disappeared = [prev_by_id[eid] for eid in disappeared_ids]

    return {
        "added": added,
        "repeated": repeated,
        "escalated": escalated,
        "disappeared": disappeared,
    }
