"""Heuristic signal ranking for intelligence events."""

from __future__ import annotations

try:
    from .models import IntelligenceEvent
except ImportError:
    from models import IntelligenceEvent


HIGH_PRIORITY_TOPICS = {
    "model_release",
    "agent",
    "mcp",
    "infra_compute",
    "eval_safety",
    "capability_jump",
    "eval_infra",
}

MEDIUM_PRIORITY_TOPICS = {
    "open_source_model",
    "enterprise_adoption",
    "funding_policy",
    "tooling_ecosystem",
}

LOW_PRIORITY_TOPICS = {
    "paper_style_explainer",
}

LOW_SIGNAL_PATTERNS = [
    "tips",
    "fun facts",
    "celebrating",
    "summer travel",
    "organizing your space",
    "headphones",
    "how to",
    "get started",
    "settings",
    "watch ",
    "dialogues",
    "browser companion",
]

CONSUMER_PRODUCT_PATTERNS = [
    "translate",
    "travel",
    "photos",
    "chrome",
    "workspace",
    "videos",
    "headphones",
    "organizing your space",
    "ads advisor",
    "google vids",
    "tts",
    "video generation",
    "satellite imagery",
    "brazil",
    "browser companion",
]

STRONG_SIGNAL_PATTERNS = [
    "agentic era",
    "orchestration",
    "compute bottleneck",
    "cybersecurity",
    "inference tiers",
    "open-source spec",
    "tpu",
    "gpu",
    "launching",
    "managed agents",
    "codex",
    "stargate",
    "higher-fidelity",
    "million-token",
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


def score_event(event: IntelligenceEvent) -> IntelligenceEvent:
    score = 0.0
    title_summary = f" {event.title} {event.summary} ".lower()

    has_structural_signal = any(p in title_summary for p in STRUCTURAL_SIGNAL_PATTERNS)
    has_policy_narrative = any(p in title_summary for p in POLICY_NARRATIVE_PATTERNS)
    is_roundup = any(p in title_summary for p in ROUNDUP_PATTERNS)

    if "official" in event.topics:
        score += 0.24

    for topic in event.topics:
        if topic in HIGH_PRIORITY_TOPICS:
            score += 0.13
        elif topic in MEDIUM_PRIORITY_TOPICS:
            score += 0.08
        elif topic in LOW_PRIORITY_TOPICS:
            score -= 0.08

    if "tutorial_enablement" in event.topics:
        score -= 0.22
    if "case_study" in event.topics:
        score -= 0.14
    if "explainer_positioning" in event.topics and not (has_structural_signal or has_policy_narrative):
        score -= 0.12
    if "roundup_recap" in event.topics or is_roundup:
        score -= 0.24
    if "paper_style_explainer" in event.topics and "capability_jump" not in event.topics and "eval_infra" not in event.topics:
        score -= 0.12

    keyword_boosts = {
        " release ": 0.10,
        " launch ": 0.10,
        " version ": 0.07,
        " agent ": 0.09,
        " agentic ": 0.10,
        " mcp ": 0.15,
        " orchestration ": 0.11,
        " security ": 0.10,
        " cybersecurity ": 0.12,
        " compute ": 0.10,
        " tpu ": 0.13,
        " gpu ": 0.13,
        " funding ": 0.08,
        " ipo ": 0.08,
        " benchmark ": 0.08,
        " eval ": 0.09,
        " reranker ": 0.05,
        " latency ": 0.06,
        " pricing ": 0.05,
        " aws ": 0.07,
        " api ": 0.04,
        " million-token ": 0.07,
        " higher-fidelity ": 0.07,
    }
    for keyword, boost in keyword_boosts.items():
        if keyword in title_summary:
            score += boost

    for phrase in STRONG_SIGNAL_PATTERNS:
        if phrase in title_summary:
            score += 0.06

    for phrase in LOW_SIGNAL_PATTERNS:
        if phrase in title_summary:
            score -= 0.20

    if any(phrase in title_summary for phrase in TUTORIAL_PATTERNS):
        score -= 0.25

    if any(phrase in title_summary for phrase in CASE_STUDY_PATTERNS):
        score -= 0.14

    if any(phrase in title_summary for phrase in EXPLAINER_PATTERNS) and not (has_structural_signal or has_policy_narrative):
        score -= 0.12

    if is_roundup:
        score -= 0.18

    consumer_hits = sum(1 for phrase in CONSUMER_PRODUCT_PATTERNS if phrase in title_summary)
    if consumer_hits >= 1:
        score -= 0.12
    if consumer_hits >= 2:
        score -= 0.10

    if "google translate" in title_summary:
        score -= 0.18
    if "ads advisor" in title_summary:
        score -= 0.18
    if "summer" in title_summary:
        score -= 0.12
    if "brazil" in title_summary or "satellite imagery" in title_summary:
        score -= 0.16
    if "chrome" in title_summary and "agent" not in title_summary and "orchestration" not in title_summary:
        score -= 0.14
    if "tts" in title_summary:
        score -= 0.10
    if "video generation" in title_summary or "veo" in title_summary:
        score -= 0.08

    score = max(0.0, min(1.0, round(score, 3)))
    event.signal_score = score
    event.metadata["signal_bucket"] = signal_bucket(score)
    event.metadata["reason"] = explain_score(event)
    event.metadata["heuristic_insight"] = explain_insight(event)
    event.metadata["watch_next"] = suggest_watch_next(event)
    return event


def explain_score(event: IntelligenceEvent) -> str:
    topics = set(event.topics)
    title_summary = f" {event.title} {event.summary} ".lower()
    has_structural_signal = any(p in title_summary for p in STRUCTURAL_SIGNAL_PATTERNS)
    has_policy_narrative = any(p in title_summary for p in POLICY_NARRATIVE_PATTERNS)
    is_roundup = any(p in title_summary for p in ROUNDUP_PATTERNS)

    reasons: list[str] = []

    if "official" in topics:
        reasons.append("官方来源")

    # Main reason by type
    if "tutorial_enablement" in topics or any(p in title_summary for p in TUTORIAL_PATTERNS):
        reasons.append("更适合帮助理解和上手，不代表新的行业主线")
    elif "case_study" in topics or any(p in title_summary for p in CASE_STUDY_PATTERNS):
        reasons.append("提供落地采用证据，可验证真实需求和业务可行性")
    elif "roundup_recap" in topics or is_roundup:
        reasons.append("属于阶段性回顾/汇总，更适合补背景而非判断新增趋势")
    elif "paper_style_explainer" in topics and "capability_jump" not in topics and "eval_infra" not in topics:
        reasons.append("更偏论文/分析说明，认知价值高于短期行业信号价值")
    elif "capability_jump" in topics:
        reasons.append("带有能力边界前移信号，可能改写现有产品形态或训练方式")
    elif "eval_infra" in topics:
        reasons.append("带有评测/验证基础设施成熟信号，关系到 Agent 从 demo 到生产")
    elif "tooling_ecosystem" in topics:
        reasons.append("带有工具链成熟度提升信号，会影响开发效率和生态采用速度")
    elif has_policy_narrative and "eval_safety" in topics:
        reasons.append("带有治理/采购口径变化信号，会影响合规、风险和企业预期")
    elif has_structural_signal and ("agent" in topics or "infra_compute" in topics or "enterprise_adoption" in topics):
        reasons.append("带有平台分层/接口重构信号，可能改变成本结构和分发格局")
    elif "model_release" in topics:
        reasons.append("带有版本迭代信号，值得看是否伴随能力或产品边界变化")

    # Secondary supporting reasons
    if "mcp" in topics:
        reasons.append("涉及 MCP 生态")
    if any(k in title_summary for k in ["launch", "release", "version"]):
        reasons.append("存在明确发布/升级动作")
    if any(k in title_summary for k in ["tpu", "gpu", "compute"]):
        reasons.append("可能影响算力成本和性能上限")
    if any(k in title_summary for k in ["latency", "pricing", "api", "aws"]):
        reasons.append("可能影响调用成本、交付方式或分发路径")

    if not reasons:
        reasons.append("作为背景补充保留")
    return "；".join(dict.fromkeys(reasons))


def explain_insight(event: IntelligenceEvent) -> str:
    topics = set(event.topics)
    title_summary = f" {event.title} {event.summary} ".lower()
    has_structural_signal = any(p in title_summary for p in STRUCTURAL_SIGNAL_PATTERNS)
    has_policy_narrative = any(p in title_summary for p in POLICY_NARRATIVE_PATTERNS)
    is_roundup = any(p in title_summary for p in ROUNDUP_PATTERNS)

    if "tutorial_enablement" in topics or any(p in title_summary for p in TUTORIAL_PATTERNS):
        return "这更像使用教程或能力说明，价值在帮助理解产品，而不是代表行业主线变化。"
    if "case_study" in topics or any(p in title_summary for p in CASE_STUDY_PATTERNS):
        return "这类内容更像 adoption 证据，能证明落地趋势，但通常不是一线前沿信号。"
    if "roundup_recap" in topics or is_roundup:
        return "这更像阶段性回顾或新闻打包汇总，适合补背景，不代表新的一级信号。"
    if "paper_style_explainer" in topics and "capability_jump" not in topics and "eval_infra" not in topics:
        return "这更像论文式分析或技术说明，帮助理解方法，但未必代表行业主线正在切换。"
    if "capability_jump" in topics:
        return "这类信号通常意味着能力边界前移，值得看它会不会改写现有产品形态或训练范式。"
    if "eval_infra" in topics:
        return "这不是单纯论文信息，而是在补评测、验证、可复现实验这一层基础设施。"
    if "tooling_ecosystem" in topics:
        return "这更像生态工具链升级，短期不一定最炸，但会影响开发效率和下游采用速度。"
    if "explainer_positioning" in topics and not (has_structural_signal or has_policy_narrative):
        return "这更像官方说明文或定位叙事，帮助塑造认知，但不等于新的行业主信号。"
    if has_policy_narrative and "eval_safety" in topics:
        return "这更像政策/安全叙事信号，影响采购、合规和行业治理预期。"
    if has_structural_signal and ("agent" in topics or "infra_compute" in topics or "enterprise_adoption" in topics):
        return "它在解释的不是功能细节，而是平台分层、协议接口或基础设施格局变化。"
    if any(p in title_summary for p in ["ads advisor", "chrome", "tts", "video generation", "brazil", "satellite imagery"]):
        return "这条更偏具体产品功能/场景落地，除非后续出现生态扩散，否则行业外溢性有限。"
    if {"infra_compute", "model_release"} & topics and "agent" in topics:
        return "这条更像产业底座升级，可能直接影响后续 Agent 能力边界和部署成本。"
    if "eval_safety" in topics and "infra_compute" in topics:
        return "它说明行业瓶颈正在从单纯训练算力，转向评测、推理和系统效率。"
    if "mcp" in topics:
        return "这类信号通常不是单点功能更新，而是生态协议层正在成熟。"
    if "model_release" in topics:
        return "这类更新值得看它是不是能力边界变化，而不只是常规版本迭代。"
    if "enterprise_adoption" in topics:
        return "更值得关注的是它是否意味着 AI 能力正在进入真实商业闭环。"
    return "这条更适合作为行业背景信号，帮助判断热点主线而不是单点噪音。"


def suggest_watch_next(event: IntelligenceEvent) -> str:
    topics = set(event.topics)
    title_summary = f" {event.title} {event.summary} ".lower()
    has_structural_signal = any(p in title_summary for p in STRUCTURAL_SIGNAL_PATTERNS)
    has_policy_narrative = any(p in title_summary for p in POLICY_NARRATIVE_PATTERNS)
    is_roundup = any(p in title_summary for p in ROUNDUP_PATTERNS)

    if "tutorial_enablement" in topics or any(p in title_summary for p in TUTORIAL_PATTERNS):
        return "继续看是否沉淀成标准工作流"
    if "case_study" in topics or any(p in title_summary for p in CASE_STUDY_PATTERNS):
        return "继续看是否被更多企业复用"
    if "roundup_recap" in topics or is_roundup:
        return "继续看是否出现真正新增发布"
    if "paper_style_explainer" in topics and "capability_jump" not in topics and "eval_infra" not in topics:
        return "继续看是否被更强结果或产品化验证"
    if "capability_jump" in topics:
        return "继续看是否进入真实产品或训练工作流"
    if "eval_infra" in topics:
        return "继续看是否被主流评测栈采用"
    if "tooling_ecosystem" in topics:
        return "继续看是否被更多框架和开发者接入"
    if "explainer_positioning" in topics and not (has_structural_signal or has_policy_narrative):
        return "继续看是否升级成正式产品动作"
    if has_policy_narrative:
        return "继续看是否落到合规产品或政策动作"
    if has_structural_signal:
        return "继续看是否改变平台分层或行业接口"
    if any(p in title_summary for p in ["ads advisor", "chrome", "tts", "video generation"]):
        return "继续看是否跨产品线扩散"
    if "infra_compute" in topics:
        return "继续看成本、吞吐和部署节奏"
    if "agent" in topics:
        return "继续看是否出现真实工作流落地"
    if "eval_safety" in topics:
        return "继续看评测基准和安全边界变化"
    if "model_release" in topics:
        return "继续看是否伴随 API / 定价 / benchmark"
    if "funding_policy" in topics:
        return "继续看是否影响资本开支和监管走向"
    return "继续看是否被更多源重复验证"


def score_events(events: list[IntelligenceEvent]) -> list[IntelligenceEvent]:
    ranked = [score_event(e) for e in events]
    ranked.sort(key=lambda e: (-e.signal_score, e.published_at, e.title.lower()))
    return ranked


def signal_bucket(score: float) -> str:
    if score >= 0.72:
        return "must_know"
    if score >= 0.48:
        return "worth_watch"
    if score >= 0.22:
        return "background"
    return "observe"
