"""Adapter interface for source ingestion."""

from __future__ import annotations

from abc import ABC, abstractmethod

try:
    from .models import SourceConfig, IngestionBatch
except ImportError:
    from models import SourceConfig, IngestionBatch


class SourceAdapter(ABC):
    @abstractmethod
    def supports(self, source: SourceConfig) -> bool:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, source: SourceConfig) -> IngestionBatch:
        raise NotImplementedError
