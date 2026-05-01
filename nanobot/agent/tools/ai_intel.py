"""AI tech intelligence tool for nanobot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import StringSchema, tool_parameters_schema
from nanobot.ai_intel import diff_events, generate_brief, load_snapshot, merge_batches, run_ingestion, save_snapshot


@tool_parameters(
    tool_parameters_schema(
        action=StringSchema(
            "daily_brief",
            description="Action to run: daily_brief | midday_recap | refresh",
            enum=["daily_brief", "midday_recap", "refresh"],
        ),
        required=["action"],
    )
)
class AITechIntelTool(Tool):
    """Generate AI intelligence briefs from tracked sources."""

    def __init__(self, workspace: Path | None = None):
        self._workspace = workspace

    @property
    def name(self) -> str:
        return "ai_intel"

    @property
    def description(self) -> str:
        return (
            "Run the AI tech intelligence pipeline and return a structured brief. "
            "Use for daily brief, midday recap, or refresh of tracked AI/LLM/Agent signals."
        )

    async def execute(self, action: str = "daily_brief", **kwargs: Any) -> str:
        batches = run_ingestion()
        merged = merge_batches(batches)
        previous = load_snapshot()
        changes = diff_events(merged, previous)
        save_snapshot(merged)

        if action == "refresh":
            return (
                f"AI intel refresh complete. "
                f"events={len(merged)} added={len(changes.get('added', []))} "
                f"repeated={len(changes.get('repeated', []))} escalated={len(changes.get('escalated', []))}"
            )

        mode = "daily" if action == "daily_brief" else "midday"
        return generate_brief(merged, mode=mode, change_summary=changes)
