"""Agent 3: price signal reader. RSI, MACD, moving-average trend, Bollinger position."""
import pandas as pd

from .. import indicators as ind
from ..data import bars_frame
from ..scoring import AgentResult, Signal, clamp

MIN_BARS = 60
CHART_BARS = 120


def run(market: dict) -> AgentResult:
    df = bars_frame(market)
    if len(df) < MIN_BARS:
        return AgentResult("technicals", status="degraded", error=f"only {len(df)} bars, need {MIN_BARS}", summary="Not enough price history.")

    close = df["close"].astype(float)
    last = float(close.iloc[-1])
    sigs: list[Signal] = []

    r = float(ind.rsi(close).iloc[-1])
    eff = 0.3 if r < 30 else -0.3 if r > 70 else 0.05 if r < 50 else -0.05 if r < 60 else 0.05
    sigs.append(Signal("RSI(14)", f"{r:.1f}", eff, "below 30 oversold, above 70 overbought"))

    m = ind.macd(close)
    hist, hist_prev = float(m["hist"].iloc[-1]), float(m["hist"].iloc[-2])
    eff = (0.25 if hist > 0 else -0.25) + (0.1 if hist > hist_prev else -0.1)
    sigs.append(Signal("MACD histogram", f"{hist:+.2f}", eff, "positive and rising means momentum is building"))

    s50 = float(ind.sma(close, 50).iloc[-1])
    sigs.append(Signal("Price vs SMA50", f"{(last / s50 - 1) * 100:+.1f}%", 0.25 if last > s50 else -0.25, "medium-term trend"))

    if len(close) >= 200:
        s200 = float(ind.sma(close, 200).iloc[-1])
        cross = s50 > s200
        sigs.append(Signal("SMA50 vs SMA200", "golden" if cross else "death", 0.25 if cross else -0.25, "long-term trend regime"))

    bb = ind.bollinger(close)
    lo, hi = float(bb["lower"].iloc[-1]), float(bb["upper"].iloc[-1])
    pos = (last - lo) / (hi - lo) if hi > lo else 0.5
    eff = 0.15 if pos < 0.15 else -0.15 if pos > 0.85 else 0.0
    sigs.append(Signal("Bollinger position", f"{pos * 100:.0f}% of band", eff, "near lower band is stretched down, near upper is stretched up"))

    atr = float(ind.atr(df["high"].astype(float), df["low"].astype(float), close).iloc[-1])
    score = clamp(sum(s.effect for s in sigs) / 1.1)

    tail = df.tail(CHART_BARS).reset_index(drop=True)
    sma20, sma50 = ind.sma(close, 20).tail(CHART_BARS), ind.sma(close, 50).tail(CHART_BARS)
    rsi_s = ind.rsi(close).tail(CHART_BARS)
    chart = {
        "dates": tail["date"].tolist(),
        "close": [round(float(v), 2) for v in tail["close"]],
        "sma20": [None if pd.isna(v) else round(float(v), 2) for v in sma20],
        "sma50": [None if pd.isna(v) else round(float(v), 2) for v in sma50],
        "rsi": [None if pd.isna(v) else round(float(v), 1) for v in rsi_s],
    }
    trend = "uptrend" if last > s50 else "downtrend"
    return AgentResult("technicals", score=score, signals=sigs,
                       summary=f"Last close {last:.2f}, {trend} vs SMA50, RSI {r:.0f}, ATR {atr:.2f}.",
                       data={"last_close": round(last, 2), "atr": round(atr, 2), "chart": chart,
                             "volatility": ind.annualized_volatility(close), "max_drawdown": ind.max_drawdown(close)})
