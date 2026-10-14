"""LangGraph pipeline: load -> (fundamentals | sentiment | technicals) in parallel -> risk_brief."""
import time
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from . import data
from .agents import fundamentals, risk_brief, sentiment, technicals
from .llm import LLMClient
from .scoring import AgentResult


class State(TypedDict, total=False):
    ticker: str
    offline: bool
    llm: LLMClient | None
    market: dict | None
    market_error: str | None
    fundamentals: AgentResult
    sentiment: AgentResult
    technicals: AgentResult
    risk_brief: AgentResult


def _guarded(name: str, fn) -> AgentResult:
    """One agent failing must never abort the run: it degrades and the rest carry on."""
    start = time.perf_counter()
    try:
        result = fn()
    except Exception as exc:  # noqa: BLE001 - boundary: any agent failure becomes a degraded result
        result = AgentResult(name, status="degraded", error=f"{type(exc).__name__}: {exc}", summary="Agent failed.")
    result.data["ms"] = int((time.perf_counter() - start) * 1000)
    return result


def _load(state: State) -> dict:
    try:
        return {"market": data.get_market(state["ticker"], state["offline"]), "market_error": None}
    except Exception as exc:  # noqa: BLE001
        return {"market": None, "market_error": str(exc)}


def _need_market(state: State, name: str, fn) -> dict:
    def go():
        if state.get("market") is None:
            raise data.DataError(state.get("market_error") or "market data unavailable")
        return fn(state["market"])
    return {name: _guarded(name, go)}


def _fundamentals(state: State) -> dict:
    return _need_market(state, "fundamentals", fundamentals.run)


def _technicals(state: State) -> dict:
    return _need_market(state, "technicals", technicals.run)


def _sentiment(state: State) -> dict:
    def go():
        return sentiment.run(data.get_news(state["ticker"], state["offline"], state.get("market")))
    return {"sentiment": _guarded("sentiment", go)}


def _brief(state: State) -> dict:
    results = {k: state[k] for k in ("fundamentals", "sentiment", "technicals") if k in state}
    return {"risk_brief": _guarded("risk_brief", lambda: risk_brief.run(state["ticker"], results, state.get("llm")))}


def build_graph():
    g = StateGraph(State)
    g.add_node("load", _load)
    g.add_node("fundamentals", _fundamentals)
    g.add_node("sentiment", _sentiment)
    g.add_node("technicals", _technicals)
    g.add_node("risk_brief", _brief)
    g.add_edge(START, "load")
    for n in ("fundamentals", "sentiment", "technicals"):
        g.add_edge("load", n)
        g.add_edge(n, "risk_brief")
    g.add_edge("risk_brief", END)
    return g.compile()


_GRAPH = None


def research(ticker: str, offline: bool = False, llm: LLMClient | None = None) -> dict[str, Any]:
    """Run the full pipeline and return a JSON-serialisable report."""
    global _GRAPH
    _GRAPH = _GRAPH or build_graph()
    ticker = data.normalize_ticker(ticker)
    if offline and ticker not in data.fixture_tickers():
        raise data.DataError(f"no offline fixture for {ticker}; available: {', '.join(data.fixture_tickers())}")
    t0 = time.perf_counter()
    out = _GRAPH.invoke({"ticker": ticker, "offline": offline, "llm": llm})
    if out.get("market") is None:
        # No prices means no fundamentals, technicals or risk: nothing worth saving. Fail loudly instead.
        raise data.DataError(out.get("market_error") or f"no market data for {ticker}")
    agents = [out[k].as_dict() for k in ("fundamentals", "sentiment", "technicals", "risk_brief")]
    brief = out["risk_brief"]
    market = out.get("market") or {}
    return {
        "ticker": ticker,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "offline" if offline else "live",
        "synthetic": bool(market.get("synthetic")),
        "llm": llm.name if llm else "none",
        "rating": brief.data.get("rating"),
        "risk_label": brief.data.get("risk_label"),
        "score": brief.data.get("adjusted"),
        "brief": brief.summary,
        "agents": agents,
        "degraded": [a["agent"] for a in agents if a["status"] != "ok"],
        "elapsed_ms": int((time.perf_counter() - t0) * 1000),
    }
