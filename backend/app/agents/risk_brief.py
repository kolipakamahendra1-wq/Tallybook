"""Agent 4: risk assessor and brief writer. Numbers come from scoring.py; the LLM only writes prose."""
from ..llm import LLMClient, LLMError
from ..scoring import AgentResult, Signal, composite, rate, risk_label, risk_level

SYSTEM = (
    "You are a cautious equity research writer. Write a 4 to 6 sentence investment brief for a retail reader. "
    "Use ONLY the numbers given. Never invent figures, prices or events. Mention the main risk. "
    "Do not give personalised advice. Plain prose, no lists, no markdown."
)


def _facts(ticker: str, results: dict[str, AgentResult], rating: str, score: float, risk: str) -> str:
    lines = [f"Ticker: {ticker}", f"Rating: {rating} (score {score:+.2f}, risk {risk})"]
    for key in ("fundamentals", "sentiment", "technicals"):
        r = results.get(key)
        if r is None:
            continue
        lines.append(f"{key}: {'DEGRADED, ' + (r.error or '') if r.status != 'ok' else f'score {r.score:+.2f}. ' + r.summary}")
    return "\n".join(lines)


def template_brief(ticker: str, results: dict[str, AgentResult], rating: str, score: float, risk: str, risk_sigs: list[Signal]) -> str:
    parts = [f"{ticker} rates {rating} with a composite score of {score:+.2f} and {risk.lower()} risk."]
    for key in ("fundamentals", "sentiment", "technicals"):
        r = results.get(key)
        if r is not None and r.status == "ok":
            parts.append(r.summary)
        elif r is not None:
            parts.append(f"The {key} agent had no usable data ({r.error}).")
    worst = max(risk_sigs, key=lambda s: s.effect)
    parts.append(f"Largest risk factor: {worst.name} at {worst.value}.")
    parts.append("Educational output, not financial advice.")
    return " ".join(parts)


def run(ticker: str, results: dict[str, AgentResult], llm: LLMClient | None) -> AgentResult:
    tech = results.get("technicals")
    fund = results.get("fundamentals")
    vol = (tech.data.get("volatility") if tech and tech.status == "ok" else None)
    dd = (tech.data.get("max_drawdown") if tech and tech.status == "ok" else None)
    if vol is None or dd is None:
        return AgentResult("risk_brief", status="degraded", error="price data unavailable, cannot assess risk",
                           summary="Risk could not be assessed without price history.")

    beta = _beta(fund)
    de = _debt(fund)
    risk, risk_sigs = risk_level(vol, dd, beta, de)
    score, weights = composite(results)
    adjusted, rating = rate(score, risk)
    rlabel = risk_label(risk)

    brief, brief_source = template_brief(ticker, results, rating, adjusted, rlabel, risk_sigs), "template"
    llm_error = None
    if llm is not None:
        try:
            text = llm.complete(SYSTEM, _facts(ticker, results, rating, adjusted, rlabel))
            if len(text) > 40:
                brief, brief_source = text, llm.name
        except LLMError as exc:
            llm_error = str(exc)  # keep the deterministic brief; surface the reason

    return AgentResult("risk_brief", score=adjusted, signals=risk_sigs, summary=brief,
                       data={"rating": rating, "composite": round(score, 3), "adjusted": round(adjusted, 3),
                             "risk": round(risk, 3), "risk_label": rlabel, "weights": {k: round(v, 3) for k, v in weights.items()},
                             "brief_source": brief_source, "llm_error": llm_error})


def _debt(fund):
    return fund.data.get("debt_to_equity") if fund is not None and fund.status == "ok" else None


def _beta(fund):
    return fund.data.get("beta") if fund is not None and fund.status == "ok" else None
