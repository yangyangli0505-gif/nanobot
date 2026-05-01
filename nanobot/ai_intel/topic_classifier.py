"""Rule-based topic classification for intelligence events."""

from __future__ import annotations

try:
    from .models import IntelligenceEvent
except ImportError:
    from models import IntelligenceEvent


TOPIC_RULES: dict[str, list[str]] = {
    "model_release": [
        " model ", " release ", " launch ", " version ", "gemini", "gpt", "claude", "llama", "granite", "tpu", "gpu",
    ],
    "agent": [
        " agent ", " agents ", " agentic ", " orchestration ", "tool use", "automation", "managed agents", "codex",
    ],
    "mcp": [
        "mcp", "model context protocol",
    ],
    "infra_compute": [
        "gpu", "tpu", "compute", "datacenter", "data center", "inference", "training", "chip", "chips", "cloud",
    ],
    "eval_safety": [
        "eval", "evaluation", "safety", "alignment", "cybersecurity", "security", "benchmark",
    ],
    "open_source_model": [
        "open source", "hugging face", "weights", "checkpoint", "granite", "mistral", "sentence transformers",
    ],
    "enterprise_adoption": [
        "enterprise", "business", "workspace", "customer", "deployment", "productivity", "aws",
    ],
    "funding_policy": [
        "funding", "investment", "capital", "policy", "regulation", "government", "acquisition", "ipo",
    ],
    "tutorial_enablement": [
        "how to", "get started", "working with", "top 10 uses", "what is ", "plugins and skills", "guide", "academy",
    ],
    "case_study": [
        "customer story", "used openai", "used our api", "automates", "case study", "how choco", "real-world ai impact",
    ],
    "explainer_positioning": [
        "learn how", "inside ", "why ", "what is ", "here’s how", "here's how", "introducing", "our commitment",
    ],
    "roundup_recap": [
        "latest ai news", "roundup", "recap", "highlights", "this month", "this week", "in march 2026", "announced in march", "what we announced",
    ],
}

NOISE_PATTERNS = [
    "fun facts",
    "travel smarter",
    "organizing your space",
    "summer",
]

CONSUMER_SURFACE_PATTERNS = [
    "chrome",
    "workspace",
    "ads advisor",
    "google vids",
    "tts",
    "video generation",
    "satellite imagery",
    "brazil",
    "browser companion",
    "translate",
    "photos",
]

STRONG_INFRA_PATTERNS = [
    "tpu",
    "gpu",
    "compute",
    "inference",
    "datacenter",
    "data center",
    "chip",
    "chips",
    "throughput",
    "latency",
    "orchestration",
    "managed agents",
    "codex",
    "mcp",
]

TUTORIAL_PATTERNS = [
    "how to",
    "get started",
    "working with",
    "plugins and skills",
    "tutorial",
    "top 10 uses",
    "what is ",
    "academy",
]

CASE_STUDY_PATTERNS = [
    "customer story",
    "used openai",
    "used our api",
    "automates",
    "case study",
    "real-world ai impact",
]

EXPLAINER_PATTERNS = [
    "learn how",
    "inside ",
    "why ",
    "what is ",
    "here’s how",
    "here's how",
    "introducing",
    "our commitment",
]

ROUNDUP_PATTERNS = [
    "latest ai news",
    "roundup",
    "recap",
    "highlights",
    "this month",
    "this week",
    "in march 2026",
    "announced in march",
    "what we announced",
]

HF_CAPABILITY_PATTERNS = [
    "higher-fidelity",
    "frontier",
    "million-token",
    "long-context",
    "multimodal intelligence",
    "can actually use",
    "interactive worlds",
]

HF_EVAL_INFRA_PATTERNS = [
    "eval",
    "benchmark",
    "verifiable",
    "failure modes",
    "bottleneck",
    "alignment",
    "guardrail",
]

HF_TOOLING_PATTERNS = [
    "inference providers",
    "reranker",
    "embedding",
    "sentence transformers",
    "gradio",
    "provider",
    "tool use",
    "sdk",
    "framework",
]

HF_PAPER_EXPLAINER_PATTERNS = [
    "how they’re built",
    "how they're built",
    "reasoning, tool use, and failure modes",
    "paper",
    "analysis",
]

STRUCTURAL_SIGNAL_PATTERNS = [
    "open-source spec",
    "spec",
    "orchestration",
    "mcp",
    "managed agents",
    "inference tiers",
    "pricing",
    "latency",
    "priority",
    "flex",
    "api",
    "aws",
    "stargate",
    "compute infrastructure",
    "tpu",
    "gpu",
    "datacenter",
    "data center",
]

POLICY_NARRATIVE_PATTERNS = [
    "cybersecurity",
    "security",
    "policy",
    "regulation",
    "government",
    "safety",
    "trust",
]


def classify_event(event: IntelligenceEvent) -> IntelligenceEvent:
    haystack = f" {event.title} {event.summary} ".lower()
    topics = set(event.topics)

    for topic, keywords in TOPIC_RULES.items():
        if any(k in haystack for k in keywords):
            topics.add(topic)

    has_structural_signal = any(pattern in haystack for pattern in STRUCTURAL_SIGNAL_PATTERNS)
    has_policy_narrative = any(pattern in haystack for pattern in POLICY_NARRATIVE_PATTERNS)
    is_roundup = any(pattern in haystack for pattern in ROUNDUP_PATTERNS)
    is_hf = event.source == "huggingface_blog"

    # tame over-tagging for clearly lightweight consumer content
    if any(pattern in haystack for pattern in NOISE_PATTERNS):
        topics.discard("infra_compute")
        topics.discard("agent")
        topics.discard("model_release")

    # consumer-facing feature posts should not automatically look like infra / agent news
    if any(pattern in haystack for pattern in CONSUMER_SURFACE_PATTERNS):
        if not any(pattern in haystack for pattern in STRONG_INFRA_PATTERNS):
            topics.discard("infra_compute")
        if not any(pattern in haystack for pattern in ["orchestration", "managed agents", "codex", "mcp"]):
            topics.discard("agent")

    # tutorials / enablement content should not look like major release signals
    if any(pattern in haystack for pattern in TUTORIAL_PATTERNS):
        topics.discard("infra_compute")
        topics.discard("model_release")
        if "mcp" not in topics:
            topics.discard("agent")

    # case studies are evidence of adoption, not frontier capability signals
    if any(pattern in haystack for pattern in CASE_STUDY_PATTERNS):
        topics.discard("infra_compute")

    # explainers are only low-signal when they do NOT explain a real structural shift
    if any(pattern in haystack for pattern in EXPLAINER_PATTERNS):
        if has_structural_signal or has_policy_narrative:
            topics.discard("explainer_positioning")
        else:
            topics.discard("infra_compute")
            if "mcp" not in topics and "agentic" not in haystack and "managed agents" not in haystack:
                topics.discard("agent")
            if not any(token in haystack for token in ["release", "launch", "version"]):
                topics.discard("model_release")

    # roundups are by definition second-order summaries, not fresh primary signals
    if is_roundup:
        topics.discard("infra_compute")
        topics.discard("agent")
        if not has_policy_narrative:
            topics.discard("model_release")

    # finer Hugging Face segmentation
    if is_hf:
        if any(pattern in haystack for pattern in HF_CAPABILITY_PATTERNS):
            topics.add("capability_jump")
            topics.discard("paper_style_explainer")
        if any(pattern in haystack for pattern in HF_EVAL_INFRA_PATTERNS):
            topics.add("eval_infra")
        if any(pattern in haystack for pattern in HF_TOOLING_PATTERNS):
            topics.add("tooling_ecosystem")
        if any(pattern in haystack for pattern in HF_PAPER_EXPLAINER_PATTERNS):
            topics.add("paper_style_explainer")

        # if it's clearly tooling/ecosystem, don't let it masquerade as capability leap
        if "tooling_ecosystem" in topics and "capability_jump" not in topics:
            topics.discard("model_release")

        # if it's paper/explainer style, keep it out of top-signal buckets unless paired with capability/eval infra
        if "paper_style_explainer" in topics and "capability_jump" not in topics and "eval_infra" not in topics:
            topics.discard("infra_compute")

    if not topics:
        topics.add("general_ai")

    event.topics = sorted(topics)
    return event


def classify_events(events: list[IntelligenceEvent]) -> list[IntelligenceEvent]:
    return [classify_event(event) for event in events]
