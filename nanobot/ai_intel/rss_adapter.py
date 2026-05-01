"""RSS source adapter."""

from __future__ import annotations

import xml.etree.ElementTree as ET
import urllib.request
from email.utils import parsedate_to_datetime

try:
    from .adapters_base import SourceAdapter
    from .models import SourceConfig, IntelligenceEvent, IngestionBatch, utc_now_iso
except ImportError:
    from adapters_base import SourceAdapter
    from models import SourceConfig, IntelligenceEvent, IngestionBatch, utc_now_iso


class RSSAdapter(SourceAdapter):
    def supports(self, source: SourceConfig) -> bool:
        return source.kind == "rss"

    def fetch(self, source: SourceConfig) -> IngestionBatch:
        events: list[IntelligenceEvent] = []
        errors: list[str] = []
        try:
            req = urllib.request.Request(source.url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                content = resp.read()
            root = ET.fromstring(content)

            items = root.findall(".//item")
            if not items:
                items = root.findall("{http://www.w3.org/2005/Atom}entry")

            for item in items[:20]:
                title = _find_text(item, ["title", "{http://www.w3.org/2005/Atom}title"]) or "Untitled"
                link = _find_text(item, ["link", "{http://www.w3.org/2005/Atom}link"]) or source.url
                if link == source.url:
                    atom_link = item.find("{http://www.w3.org/2005/Atom}link")
                    if atom_link is not None:
                        link = atom_link.attrib.get("href", source.url)
                summary = (
                    _find_text(item, ["description", "summary", "{http://www.w3.org/2005/Atom}summary"]) or ""
                )
                published = (
                    _find_text(item, ["pubDate", "published", "updated", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"]) or utc_now_iso()
                )
                published_iso = _to_iso(published)
                event = IntelligenceEvent(
                    title=title.strip(),
                    summary=_strip_html(summary).strip(),
                    url=link.strip(),
                    source=source.name,
                    published_at=published_iso,
                    topics=list(source.tags),
                    metadata={"source_kind": source.kind},
                )
                event.ensure_id()
                events.append(event)
        except Exception as e:
            errors.append(f"{type(e).__name__}: {e}")

        return IngestionBatch(
            source=source.name,
            fetched_at=utc_now_iso(),
            events=events,
            errors=errors,
        )


def _find_text(node, tags: list[str]) -> str | None:
    for tag in tags:
        child = node.find(tag)
        if child is not None and child.text:
            return child.text
    return None


def _to_iso(value: str) -> str:
    try:
        dt = parsedate_to_datetime(value)
        return dt.isoformat()
    except Exception:
        return value


def _strip_html(text: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
