"""Core data models for AI Tech Intelligence Agent."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any
import hashlib
import json


@dataclass
class SourceConfig:
    name: str
    kind: str  # rss | github_releases | html | api
    url: str
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    fetch_interval_min: int = 60
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceEvent:
    title: str
    summary: str
    url: str
    source: str
    published_at: str
    topics: list[str] = field(default_factory=list)
    signal_score: float = 0.0
    related_entities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: str = ""

    def ensure_id(self) -> str:
        if self.event_id:
            return self.event_id
        base = {
            "title": self.title.strip(),
            "url": self.url.strip(),
            "source": self.source.strip(),
            "published_at": self.published_at.strip(),
        }
        raw = json.dumps(base, ensure_ascii=False, sort_keys=True)
        self.event_id = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
        return self.event_id

    def to_dict(self) -> dict[str, Any]:
        self.ensure_id()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntelligenceEvent":
        event = cls(**data)
        event.ensure_id()
        return event


@dataclass
class IngestionBatch:
    source: str
    fetched_at: str
    events: list[IntelligenceEvent]
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "fetched_at": self.fetched_at,
            "events": [e.to_dict() for e in self.events],
            "errors": self.errors,
        }


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
