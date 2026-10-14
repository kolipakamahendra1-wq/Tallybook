"""Generate SYNTHETIC offline fixtures (seeded random walks, invented fundamentals and headlines).

They exist so demos and tests run with no network. They are not real market data.
Run: python scripts/make_fixtures.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "fixtures"

SPECS = {
    "AAPL": dict(seed=11, start=171.4, drift=0.0006, vol=0.013, info=dict(
        longName="Apple Inc. (sample)", sector="Technology", marketCap=2.91e12, trailingPE=29.7, forwardPE=26.4,
        profitMargins=0.241, revenueGrowth=0.048, debtToEquity=151.9, returnOnEquity=1.472, beta=1.21, currentRatio=0.99),
        news=[
            ("Services revenue climbs to a record as installed base widens", "Sample Wire"),
            ("Analysts raise price targets after strong iPhone demand in emerging markets", "Sample Markets"),
            ("Regulators open review of App Store payment rules", "Sample Times"),
            ("Supplier warns of component shortage that could delay a product launch", "Sample Wire"),
            ("Buyback expanded as cash flow beats expectations", "Sample Markets")]),
    "NVDA": dict(seed=23, start=462.8, drift=0.0019, vol=0.027, info=dict(
        longName="NVIDIA Corporation (sample)", sector="Technology", marketCap=1.74e12, trailingPE=68.3, forwardPE=37.1,
        profitMargins=0.489, revenueGrowth=1.262, debtToEquity=41.2, returnOnEquity=0.912, beta=1.68, currentRatio=4.17),
        news=[
            ("Data center orders surge, guidance far above consensus", "Sample Wire"),
            ("Chip export curbs could cut into next quarter sales, firm says", "Sample Times"),
            ("Rival unveils accelerator aimed at closing the performance gap", "Sample Markets"),
            ("Record profit lifts shares as demand outstrips supply", "Sample Wire"),
            ("Valuation worries grow after a steep rally", "Sample Markets")]),
    "TSLA": dict(seed=37, start=248.9, drift=-0.0004, vol=0.031, info=dict(
        longName="Tesla, Inc. (sample)", sector="Consumer Cyclical", marketCap=7.9e11, trailingPE=74.6, forwardPE=61.8,
        profitMargins=0.153, revenueGrowth=0.037, debtToEquity=17.8, returnOnEquity=0.231, beta=2.34, currentRatio=1.73),
        news=[
            ("Deliveries miss estimates as price cuts squeeze margins", "Sample Wire"),
            ("Recall covers vehicles over software fault, regulator says", "Sample Times"),
            ("Energy storage unit posts strong growth", "Sample Markets"),
            ("Analyst downgrade cites slowing demand and rising competition", "Sample Markets"),
            ("Investors weigh lawsuit risk as probe widens", "Sample Wire")]),
}


def build(ticker: str, spec: dict) -> dict:
    rng = np.random.default_rng(spec["seed"])
    n = 260
    rets = rng.normal(spec["drift"], spec["vol"], n)
    close = spec["start"] * np.exp(np.cumsum(rets))
    spread = np.abs(rng.normal(0, spec["vol"] * 0.6, n)) * close
    high, low = close + spread, close - spread
    volume = rng.integers(18_000_000, 91_000_000, n)
    dates = pd.bdate_range(end="2025-06-27", periods=n)
    bars = [
        {"date": d.strftime("%Y-%m-%d"), "high": round(float(h), 2), "low": round(float(l), 2),
         "close": round(float(c), 2), "volume": int(v)}
        for d, h, l, c, v in zip(dates, high, low, close, volume)
    ]
    news = [{"title": t, "source": s, "published": dates[-1 - i].strftime("%Y-%m-%d")} for i, (t, s) in enumerate(spec["news"])]
    return {"ticker": ticker, "synthetic": True, "info": spec["info"], "bars": bars, "news": news}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for t, spec in SPECS.items():
        (OUT / f"{t}.json").write_text(json.dumps(build(t, spec)), encoding="utf-8")
        print("wrote", t)
