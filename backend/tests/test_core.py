import numpy as np
import pandas as pd
import pytest

from app import data, indicators as ind
from app.agents import fundamentals, sentiment, technicals
from app.scoring import AgentResult, Signal, composite, rate, risk_label


def series(values):
    return pd.Series(values, dtype=float)


# ---- indicators (data:analyze style sanity checks: range, nulls, known values)
def test_rsi_bounds_and_extremes():
    up = ind.rsi(series(range(1, 60)))
    assert up.iloc[-1] == 100.0
    down = ind.rsi(series(range(60, 1, -1)))
    assert down.iloc[-1] < 1
    flat = ind.rsi(series([10] * 40))
    assert flat.iloc[-1] == 50.0
    rng = np.random.default_rng(1)
    noisy = ind.rsi(series(100 + rng.normal(0, 1, 300).cumsum())).dropna()
    assert noisy.between(0, 100).all()


def test_sma_known_value():
    assert ind.sma(series([1, 2, 3, 4, 5]), 5).iloc[-1] == 3


def test_macd_hist_is_line_minus_signal():
    m = ind.macd(series(np.linspace(100, 140, 80)))
    assert np.allclose(m["hist"], m["macd"] - m["signal"])


def test_bollinger_ordering():
    b = ind.bollinger(series(100 + np.sin(np.arange(60)))).dropna()
    assert (b["upper"] >= b["mid"]).all() and (b["mid"] >= b["lower"]).all()


def test_drawdown_and_volatility():
    assert ind.max_drawdown(series([100, 120, 90, 110])) == pytest.approx(-0.25)
    assert ind.max_drawdown(series([])) == 0.0
    assert ind.annualized_volatility(series([100])) == 0.0
    assert ind.annualized_volatility(series([100, 101, 99, 102, 98])) > 0


# ---- scoring
def test_composite_renormalizes_when_agent_degrades():
    ok = AgentResult("fundamentals", score=0.8)
    bad = AgentResult("sentiment", status="degraded")
    tech = AgentResult("technicals", score=0.2)
    score, w = composite({"fundamentals": ok, "sentiment": bad, "technicals": tech})
    assert set(w) == {"fundamentals", "technicals"}
    assert sum(w.values()) == pytest.approx(1.0)
    assert score == pytest.approx(0.8 * 0.35 / 0.75 + 0.2 * 0.40 / 0.75)


def test_composite_all_degraded_is_zero():
    assert composite({"fundamentals": AgentResult("fundamentals", status="degraded")}) == (0.0, {})


def test_risk_haircut_only_shrinks_bullish():
    assert rate(0.6, 1.0)[0] == pytest.approx(0.36)
    assert rate(-0.6, 1.0)[0] == pytest.approx(-0.6)
    assert rate(0.3, 0.0)[1] == "Buy"
    assert rate(0.3, 1.0)[1] == "Hold"  # haircut drops 0.30 to 0.18
    assert rate(-0.3, 0.5)[1] == "Sell"


def test_risk_label_bands():
    assert [risk_label(x) for x in (0.1, 0.4, 0.8)] == ["Low", "Moderate", "High"]


# ---- agents on fixtures
def fx(t):
    return data.get_market(t, offline=True)


def test_fundamentals_scores_in_range_and_degrades_on_sparse_info():
    r = fundamentals.run(fx("AAPL"))
    assert r.status == "ok" and -1 <= r.score <= 1 and len(r.signals) >= 5
    sparse = fundamentals.run({"ticker": "X", "info": {"trailingPE": 12}})
    assert sparse.status == "degraded"


def test_fundamentals_ignores_nan_and_strings():
    r = fundamentals.run({"ticker": "X", "info": {"trailingPE": float("nan"), "profitMargins": "n/a"}})
    assert r.status == "degraded"


def test_sentiment_lexicon_and_negation():
    assert sentiment.score_headline("Record profit as demand surges") > 0
    assert sentiment.score_headline("Recall and lawsuit hit shares") < 0
    assert sentiment.score_headline("Firm does not miss estimates") > 0
    assert sentiment.score_headline("Company holds annual meeting") == 0


def test_sentiment_empty_degrades():
    assert sentiment.run([]).status == "degraded"
    assert sentiment.run([{"title": ""}]).status == "degraded"


def test_technicals_chart_payload_aligned():
    r = technicals.run(fx("NVDA"))
    c = r.data["chart"]
    assert r.status == "ok" and -1 <= r.score <= 1
    assert len({len(c[k]) for k in ("dates", "close", "sma20", "sma50", "rsi")}) == 1
    assert 0 < r.data["volatility"] < 2 and r.data["max_drawdown"] <= 0


def test_technicals_short_history_degrades():
    m = fx("AAPL")
    short = {**m, "bars": m["bars"][:30]}
    assert technicals.run(short).status == "degraded"


# ---- data layer
def test_ticker_validation():
    assert data.normalize_ticker(" aapl ") == "AAPL"
    assert data.normalize_ticker("brk-b") == "BRK-B"
    for bad in ("", "../etc", "A B", "WAYTOOLONGTICKER", "1ABC"):
        with pytest.raises(data.DataError):
            data.normalize_ticker(bad)


def test_unknown_offline_ticker_lists_available():
    with pytest.raises(data.DataError, match="AAPL"):
        data.get_market("ZZZZ", offline=True)


def test_fixtures_flagged_synthetic():
    assert all(fx(t)["synthetic"] for t in data.fixture_tickers())


def test_signal_dict_roundtrip():
    assert Signal("a", "1", 0.12345, "n").as_dict()["effect"] == 0.123
