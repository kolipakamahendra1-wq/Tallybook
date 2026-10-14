"""Agent 2: news sentiment scanner. Finance-lexicon scoring per headline, aggregated with recency weight."""
import re

from ..scoring import AgentResult, Signal, clamp

POSITIVE = {"record", "surge", "surges", "beat", "beats", "raise", "raises", "strong", "growth", "climbs", "upgrade", "profit",
            "expanded", "buyback", "outperform", "rally", "gain", "gains", "wins", "approval", "demand", "above"}
NEGATIVE = {"miss", "misses", "cut", "cuts", "recall", "probe", "lawsuit", "downgrade", "warns", "warning", "delay", "shortage",
            "slowing", "decline", "falls", "drop", "risk", "worries", "curbs", "regulators", "fine", "investigation", "squeeze", "weak"}
NEGATORS = {"not", "no", "without", "fails", "failed"}


def score_headline(title: str) -> float:
    words = re.findall(r"[a-z']+", title.lower())
    total = 0.0
    for i, w in enumerate(words):
        sign = 1.0 if w in POSITIVE else -1.0 if w in NEGATIVE else 0.0
        if sign and i > 0 and words[i - 1] in NEGATORS:
            sign = -sign
        total += sign
    return clamp(total / 2)


def run(news: list[dict]) -> AgentResult:
    items = [n for n in news if n.get("title")]
    if not items:
        return AgentResult("sentiment", status="degraded", error="no headlines available", summary="No news to scan.")

    scored = []
    for i, n in enumerate(items):
        weight = 1 / (1 + 0.15 * i)  # sources arrive newest first
        scored.append((n, score_headline(n["title"]), weight))

    score = clamp(sum(s * w for _, s, w in scored) / sum(w for _, _, w in scored))
    pos = sum(1 for _, s, _ in scored if s > 0)
    neg = sum(1 for _, s, _ in scored if s < 0)
    signals = [Signal(n["title"][:90], f"{s:+.2f}", s * w, f"{n.get('source', '')} {n.get('published', '')}".strip()) for n, s, w in scored]
    return AgentResult("sentiment", score=score, signals=signals,
                       summary=f"{len(items)} headlines: {pos} positive, {neg} negative, {len(items) - pos - neg} neutral.",
                       data={"headlines": len(items), "positive": pos, "negative": neg})
