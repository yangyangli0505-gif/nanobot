"""Source registry loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

try:
    from .models import SourceConfig
except ImportError:
    from models import SourceConfig


DEFAULT_SOURCES_PATH = Path(__file__).with_name("sources.json")


def load_sources(path: str | Path | None = None) -> list[SourceConfig]:
    p = Path(path) if path else DEFAULT_SOURCES_PATH
    data = json.loads(p.read_text(encoding="utf-8"))
    return [SourceConfig(**item) for item in data]


def enabled_sources(sources: Iterable[SourceConfig]) -> list[SourceConfig]:
    return [s for s in sources if s.enabled]
