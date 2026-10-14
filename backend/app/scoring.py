"""Deterministic scoring. Every number in a brief comes from here, never from the LLM."""
from dataclasses import dataclass, field

WEIGHTS = {"fundamentals": 0.35, "sentiment": 0.25, "technicals": 0.40}
BUY_AT, SELL_AT = 0.25, -0.25


def clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class Signal:
    name: str
    value: str
    effect: float  # contribution to the agent score, before clamping
    note: str

    def as_dict(self) -> dict:
        return {"name": self.name, "value": self.value, "effect": round(self.effect, 3), "note": self.note}


@dataclass
class AgentResult:
    agent: str
    status: str = "ok"  # ok | degraded
    score: float = 0.0
    signals: list = field(default_factory=list)
    summary: str = ""
    error: str | None = None
    data: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"agent": self.agent, "status": self.status, "score": round(self.score, 3),
                "signals": [s.as_dict() if isinstance(s, Signal) else s for s in self.signals],
                "summary": self.summary, "error": self.error, "data": self.data}


def composite(results: dict[str, AgentResult]) -> tuple[float, dict[str, float]]:
    """Weighted mean over agents that produced data; weights renormalize when one degrades."""
    live = {k: r for k, r in results.items() if r.status == "ok" and k in WEIGHTS}
    total = sum(WEIGHTS[k] for k in live)
    if total == 0:
        return 0.0, {}
    used = {k: WEIGHTS[k] / total for k in live}
    return clamp(sum(live[k].score * w for k, w in used.items())), used


def risk_level(vol: float, drawdown: float, beta: float | None, debt_to_equity: float | None) -> tuple[float, list[Signal]]:
    """Returns risk 0..1 and the contributing signals."""
    sigs, parts = [], []
    v = clamp(vol / 0.60, 0, 1)
    parts.append(v)
    sigs.append(Signal("Volatility", f"{vol * 100:.1f}% annualized", v, "above 40% is high for a large cap"))
    d = clamp(abs(drawdown) / 0.50, 0, 1)
    parts.append(d)
    sigs.append(Signal("Max drawdown", f"{drawdown * 100:.1f}%", d, "worst peak-to-trough over the window"))
    if beta is not None:
        b = clamp((beta - 0.8) / 1.6, 0, 1)
        parts.append(b)
        sigs.append(Signal("Beta", f"{beta:.2f}", b, "sensitivity to the market"))
    if debt_to_equity is not None:
        le = clamp(debt_to_equity / 300, 0, 1)
        parts.append(le)
        sigs.append(Signal("Debt to equity", f"{debt_to_equity:.1f}", le, "leverage"))
    return sum(parts) / len(parts), sigs


def rate(score: float, risk: float) -> tuple[float, str]:
    """Risk haircut shrinks bullish conviction by up to 40%; bearish scores are left alone."""
    adjusted = score * (1 - 0.4 * risk) if score > 0 else score
    label = "Buy" if adjusted >= BUY_AT else "Sell" if adjusted <= SELL_AT else "Hold"
    return clamp(adjusted), label


def risk_label(risk: float) -> str:
    return "High" if risk >= 0.6 else "Moderate" if risk >= 0.35 else "Low"
