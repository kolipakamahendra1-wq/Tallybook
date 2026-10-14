"""Agent 1: financial data analyst. Rule-based scoring of valuation, profitability, growth and balance sheet."""
from ..scoring import AgentResult, Signal, clamp


def _num(info: dict, key: str):
    v = info.get(key)
    return float(v) if isinstance(v, (int, float)) and v == v else None


def run(market: dict) -> AgentResult:
    info = market.get("info", {})
    sigs: list[Signal] = []

    pe = _num(info, "trailingPE")
    if pe is not None and pe > 0:
        eff = 0.35 if pe < 15 else 0.1 if pe < 25 else -0.1 if pe < 40 else -0.35
        sigs.append(Signal("P/E (trailing)", f"{pe:.1f}", eff, "cheap under 15, rich over 40"))

    fpe = _num(info, "forwardPE")
    if pe and fpe and fpe > 0:
        eff = 0.2 if fpe < pe * 0.85 else -0.15 if fpe > pe else 0.0
        sigs.append(Signal("Forward vs trailing P/E", f"{fpe:.1f} vs {pe:.1f}", eff, "falling P/E implies expected earnings growth"))

    pm = _num(info, "profitMargins")
    if pm is not None:
        eff = 0.35 if pm > 0.25 else 0.15 if pm > 0.10 else -0.1 if pm > 0 else -0.4
        sigs.append(Signal("Profit margin", f"{pm * 100:.1f}%", eff, "net income over revenue"))

    rg = _num(info, "revenueGrowth")
    if rg is not None:
        eff = 0.4 if rg > 0.20 else 0.15 if rg > 0.05 else -0.05 if rg >= 0 else -0.35
        sigs.append(Signal("Revenue growth", f"{rg * 100:.1f}%", eff, "year over year"))

    roe = _num(info, "returnOnEquity")
    if roe is not None:
        eff = 0.25 if roe > 0.20 else 0.1 if roe > 0.10 else -0.15
        sigs.append(Signal("Return on equity", f"{roe * 100:.1f}%", eff, "profit generated per unit of equity"))

    de = _num(info, "debtToEquity")
    if de is not None:
        eff = 0.15 if de < 50 else -0.05 if de < 150 else -0.25
        sigs.append(Signal("Debt to equity", f"{de:.1f}", eff, "higher means more leverage"))

    cr = _num(info, "currentRatio")
    if cr is not None:
        eff = 0.1 if cr >= 1.5 else -0.1 if cr < 1.0 else 0.0
        sigs.append(Signal("Current ratio", f"{cr:.2f}", eff, "short-term liquidity"))

    if len(sigs) < 3:
        return AgentResult("fundamentals", status="degraded", signals=sigs,
                           error="fewer than 3 fundamental metrics available", summary="Not enough fundamentals to score.")

    score = clamp(sum(s.effect for s in sigs) / 1.2)
    top = max(sigs, key=lambda s: abs(s.effect))
    name = info.get("longName") or market.get("ticker")
    return AgentResult("fundamentals", score=score, signals=sigs,
                       summary=f"{name}: {len(sigs)} metrics scored. Largest factor: {top.name} at {top.value} ({'+' if top.effect > 0 else '-'}).",
                       data={"sector": info.get("sector"), "market_cap": _num(info, "marketCap"), "name": name,
                             "beta": _num(info, "beta"), "debt_to_equity": de})
