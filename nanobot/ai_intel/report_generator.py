"""Report generation for daily brief / midday recap."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

try:
    from .models import IntelligenceEvent
    from .signal_ranker import signal_bucket
except ImportError:
    from models import IntelligenceEvent
    from signal_ranker import signal_bucket


TITLE_MAP = {
    "must_know": "必须知道",
    "worth_watch": "值得关注",
    "background": "背景补充",
    "observe": "待观察",
}


def generate_brief(
    events: list[IntelligenceEvent],
    mode: str = "daily",
    change_summary: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc).astimezone()
    title = "AI Tech Intelligence Daily Brief" if mode == "daily" else "AI Tech Intelligence Midday Recap"

    groups: dict[str, list[IntelligenceEvent]] = defaultdict(list)
    for event in events:
        groups[signal_bucket(event.signal_score)].append(event)

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"生成时间：{now.strftime('%Y-%m-%d %H:%M %Z')}")
    lines.append("")

    if change_summary:
        added = len(change_summary.get("added", []))
        escalated = len(change_summary.get("escalated", []))
        repeated = len(change_summary.get("repeated", []))
        lines.append(f"变化摘要：新增 {added} 条，升温 {escalated} 条，重复延续 {repeated} 条。")
        lines.append("")

    lines.extend(_headline_section(events))

    if change_summary and change_summary.get("added"):
        lines.append("## 新增变化")
        lines.append("")
        for event in change_summary["added"][:6]:
            lines.append(f"- **{event.title}** ({event.source})")
        lines.append("")

    if change_summary and change_summary.get("escalated"):
        lines.append("## 持续升温")
        lines.append("")
        for event in change_summary["escalated"][:4]:
            lines.append(f"- **{event.title}** ({event.source})")
        lines.append("")

    for bucket in ["must_know", "worth_watch", "background", "observe"]:
        bucket_events = groups.get(bucket, [])
        if not bucket_events:
            continue
        lines.append(f"## {TITLE_MAP[bucket]}")
        lines.append("")
        for event in bucket_events[:8 if bucket != 'background' else 5]:
            topic_str = ", ".join(event.topics[:4]) if event.topics else "uncategorized"
            lines.append(f"- **{event.title}**")
            if event.summary:
                lines.append(f"  - 摘要：{event.summary[:220]}")
            reason = event.metadata.get("reason") if isinstance(event.metadata, dict) else None
            if reason:
                lines.append(f"  - 为什么值得看：{reason}")
            insight = event.metadata.get("llm_insight") or event.metadata.get("heuristic_insight")
            if insight:
                lines.append(f"  - 洞察：{insight}")
            watch_next = event.metadata.get("watch_next")
            if watch_next:
                lines.append(f"  - 后续关注：{watch_next}")
            lines.append(f"  - 来源：{event.source}")
            lines.append(f"  - 主题：{topic_str}")
            lines.append(f"  - 信号分：{event.signal_score:.2f}")
            lines.append(f"  - 链接：{event.url}")
        lines.append("")

    lines.append("## Top Topics")
    lines.append("")
    topic_counts = _count_topics(events)
    for topic, count in topic_counts[:8]:
        lines.append(f"- {topic}: {count}")
    lines.append("")

    return "\n".join(lines).strip() + "\n"


def _headline_section(events: list[IntelligenceEvent]) -> list[str]:
    lines: list[str] = []
    top = events[:3]
    lines.append("一句话总结：今天最值得看的，优先是高优先级发布、Agent / orchestration、算力基础设施以及 eval / safety 信号。")
    lines.append("")
    if top:
        lines.append("## 今日最重要 3 条")
        lines.append("")
        for event in top:
            insight = event.metadata.get("llm_insight") or event.metadata.get("heuristic_insight") or "高优先级事件"
            lines.append(f"- **{event.title}**：{insight}")
        lines.append("")
    return lines


def _count_topics(events: list[IntelligenceEvent]) -> list[tuple[str, int]]:
    counter: dict[str, int] = defaultdict(int)
    for event in events:
        for topic in event.topics:
            counter[topic] += 1
    return sorted(counter.items(), key=lambda x: (-x[1], x[0]))
