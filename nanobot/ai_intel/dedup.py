"""Stable deduplication for intelligence events."""

from __future__ import annotations

import re
from urllib.parse import urlparse

try:
    from .models import IntelligenceEvent
except ImportError:
    from models import IntelligenceEvent


def dedup_events(events: list[IntelligenceEvent]) -> list[IntelligenceEvent]:
    """Deduplicate events using layered keys.

    Priority:
    1. exact event_id
    2. normalized url
    3. source-agnostic normalized title
    """
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    deduped: list[IntelligenceEvent] = []

    for event in events:
        eid = event.ensure_id()
        if eid in seen_ids:
            continue

        norm_url = normalize_url(event.url)
        if norm_url and norm_url in seen_urls:
            continue

        norm_title = normalize_title(event.title)
        if norm_title and norm_title in seen_titles:
            continue

        seen_ids.add(eid)
        if norm_url:
            seen_urls.add(norm_url)
        if norm_title:
            seen_titles.add(norm_title)
        deduped.append(event)

    return deduped


def normalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    path = parsed.path.rstrip("/")
    return f"{parsed.netloc.lower()}{path}"


def normalize_title(title: str) -> str:
    if not title:
        return ""
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\u4e00-\u9fff\s]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s
