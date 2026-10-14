"""Market + news data access. `offline=True` reads bundled synthetic fixtures; otherwise live sources."""
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import httpx
import pandas as pd

from ..config import get_settings

FIXTURES = Path(__file__).parent / "fixtures"
_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")
_CACHE: dict[str, tuple[float, dict]] = {}
CACHE_TTL = 300


class DataError(RuntimeError):
    pass


def normalize_ticker(raw: str) -> str:
    t = (raw or "").strip().upper()
    if not _TICKER_RE.match(t):
        raise DataError(f"invalid ticker '{raw}'")
    return t


def fixture_tickers() -> list[str]:
    return sorted(p.stem for p in FIXTURES.glob("*.json"))


def _load_fixture(ticker: str) -> dict:
    path = FIXTURES / f"{ticker}.json"
    if not path.exists():
        raise DataError(f"no offline fixture for {ticker}; available: {', '.join(fixture_tickers())}")
    return json.loads(path.read_text(encoding="utf-8"))


def _live_market(ticker: str) -> dict:
    import yfinance as yf  # imported lazily so offline use and tests never touch the network

    tk = yf.Ticker(ticker)
    hist = tk.history(period="1y", interval="1d", auto_adjust=True)
    if hist is None or hist.empty:
        raise DataError(f"no price history returned for {ticker}")
    bars = [
        {"date": idx.strftime("%Y-%m-%d"), "high": float(r["High"]), "low": float(r["Low"]),
         "close": float(r["Close"]), "volume": int(r["Volume"])}
        for idx, r in hist.iterrows()
    ]
    try:
        info = tk.info or {}
    except Exception:  # yfinance info scraping is flaky; fundamentals degrade, prices still work
        info = {}
    return {"ticker": ticker, "synthetic": False, "info": info, "bars": bars, "news": []}


def _alpha_overview(ticker: str, key: str) -> dict:
    resp = httpx.get("https://www.alphavantage.co/query", params={"function": "OVERVIEW", "symbol": ticker, "apikey": key}, timeout=15)
    data = resp.json() if resp.status_code == 200 else {}

    def f(name):
        try:
            return float(data[name])
        except (KeyError, TypeError, ValueError):
            return None

    mapping = {"trailingPE": f("PERatio"), "forwardPE": f("ForwardPE"), "profitMargins": f("ProfitMargin"),
               "revenueGrowth": f("QuarterlyRevenueGrowthYOY"), "returnOnEquity": f("ReturnOnEquityTTM"), "beta": f("Beta")}
    return {k: v for k, v in mapping.items() if v is not None}


def get_market(ticker: str, offline: bool) -> dict:
    ticker = normalize_ticker(ticker)
    if offline:
        return _load_fixture(ticker)
    hit = _CACHE.get(ticker)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]
    data = _live_market(ticker)
    key = get_settings().alphavantage_api_key
    if key:
        try:
            for k, v in _alpha_overview(ticker, key).items():
                data["info"].setdefault(k, v)
        except httpx.HTTPError:
            pass  # optional enrichment only
    _CACHE[ticker] = (time.time(), data)
    return data


def bars_frame(market: dict) -> pd.DataFrame:
    df = pd.DataFrame(market["bars"])
    if df.empty:
        raise DataError("no price bars")
    return df


def _google_news_rss(ticker: str) -> list[dict]:
    resp = httpx.get("https://news.google.com/rss/search", params={"q": f"{ticker} stock", "hl": "en-US", "gl": "US", "ceid": "US:en"},
                     timeout=15, follow_redirects=True)
    resp.raise_for_status()
    out = []
    for item in ET.fromstring(resp.text).iter("item"):
        out.append({"title": (item.findtext("title") or "").strip(), "source": (item.findtext("source") or "Google News"),
                    "published": (item.findtext("pubDate") or "")[:16]})
        if len(out) >= 12:
            break
    return out


def _newsapi(ticker: str, key: str) -> list[dict]:
    resp = httpx.get("https://newsapi.org/v2/everything", params={"q": ticker, "language": "en", "sortBy": "publishedAt", "pageSize": 12, "apiKey": key}, timeout=15)
    resp.raise_for_status()
    return [{"title": a["title"], "source": a["source"]["name"], "published": a["publishedAt"][:10]} for a in resp.json().get("articles", []) if a.get("title")]


def get_news(ticker: str, offline: bool, market: dict | None = None) -> list[dict]:
    ticker = normalize_ticker(ticker)
    if offline:
        return (market or _load_fixture(ticker))["news"]
    key = get_settings().newsapi_key
    errors = []
    for fetch in ([lambda: _newsapi(ticker, key)] if key else []) + [lambda: _google_news_rss(ticker)]:
        try:
            items = fetch()
            if items:
                return items
        except Exception as exc:
            errors.append(str(exc))
    raise DataError(f"no news available for {ticker} ({'; '.join(errors) or 'empty result'})")
