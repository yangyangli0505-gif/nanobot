"""Minimal ingestion pipeline."""

from __future__ import annotations

try:
    from .models import IngestionBatch
    from .source_registry import load_sources, enabled_sources
    from .rss_adapter import RSSAdapter
    from .dedup import dedup_events
    from .topic_classifier import classify_events
    from .signal_ranker import score_events
    from .llm_enricher import enrich_events
    from .report_generator import generate_brief
    from .change_detection import load_snapshot, save_snapshot, diff_events
except ImportError:
    from models import IngestionBatch
    from source_registry import load_sources, enabled_sources
    from rss_adapter import RSSAdapter
    from dedup import dedup_events
    from topic_classifier import classify_events
    from signal_ranker import score_events
    from llm_enricher import enrich_events
    from report_generator import generate_brief
    from change_detection import load_snapshot, save_snapshot, diff_events


ADAPTERS = [RSSAdapter()]


def run_ingestion() -> list[IngestionBatch]:
    batches: list[IngestionBatch] = []
    for source in enabled_sources(load_sources()):
        adapter = _pick_adapter(source)
        if adapter is None:
            batches.append(IngestionBatch(source=source.name, fetched_at="", events=[], errors=[f"No adapter for kind={source.kind}"]))
            continue
        batch = adapter.fetch(source)
        batch.events = score_events(classify_events(dedup_events(batch.events)))
        batches.append(batch)
    return batches


def merge_batches(batches: list[IngestionBatch]):
    all_events = []
    for batch in batches:
        all_events.extend(batch.events)
    merged = score_events(classify_events(dedup_events(all_events)))
    return enrich_events(merged)


def _pick_adapter(source):
    for adapter in ADAPTERS:
        if adapter.supports(source):
            return adapter
    return None


if __name__ == "__main__":
    batches = run_ingestion()
    for batch in batches:
        print(f"\n=== {batch.source} ===")
        print(f"events={len(batch.events)} errors={len(batch.errors)}")
        for err in batch.errors:
            print(f"  ERROR: {err}")
        for event in batch.events[:3]:
            print(f"- {event.title} | {event.published_at} | {', '.join(event.topics)} | {event.signal_score:.2f}")

    merged = merge_batches(batches)
    previous = load_snapshot()
    changes = diff_events(merged, previous)
    save_snapshot(merged)

    print(f"\n=== merged ===")
    print(f"events={len(merged)}")
    print(f"added={len(changes['added'])} repeated={len(changes['repeated'])} escalated={len(changes['escalated'])}")
    for event in merged[:5]:
        print(f"- {event.title} | {', '.join(event.topics)} | {event.signal_score:.2f}")

    print("\n=== brief preview ===\n")
    print(generate_brief(merged, mode="daily", change_summary=changes))
