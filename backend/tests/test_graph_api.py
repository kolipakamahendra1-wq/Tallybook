import pytest
from fastapi.testclient import TestClient

from app import graph, main, store
from app.config import Settings
from app.llm import FakeClient, LLMError


def test_full_pipeline_offline_no_llm():
    r = graph.research("NVDA", offline=True)
    assert r["rating"] in {"Buy", "Hold", "Sell"}
    assert [a["agent"] for a in r["agents"]] == ["fundamentals", "sentiment", "technicals", "risk_brief"]
    assert r["degraded"] == [] and r["synthetic"] is True and r["llm"] == "none"
    assert "not financial advice" in r["brief"]


def test_llm_writes_brief_when_available():
    llm = FakeClient("NVDA looks strong on growth but volatility is the key risk to watch closely here.")
    r = graph.research("NVDA", offline=True, llm=llm)
    assert r["brief"].startswith("NVDA looks strong") and llm.calls == 1
    assert r["agents"][3]["data"]["brief_source"] == "fake"


def test_llm_failure_falls_back_to_template():
    r = graph.research("AAPL", offline=True, llm=FakeClient(fail=True))
    risk = r["agents"][3]
    assert "rates" in r["brief"] and risk["data"]["brief_source"] == "template"
    assert "fake failure" in risk["data"]["llm_error"]


def test_short_llm_reply_is_rejected():
    r = graph.research("AAPL", offline=True, llm=FakeClient("ok"))
    assert r["agents"][3]["data"]["brief_source"] == "template"


def test_one_agent_crash_degrades_without_aborting(monkeypatch):
    def boom(_):
        raise ValueError("kaput")
    monkeypatch.setattr(graph.sentiment, "run", boom)
    r = graph.research("TSLA", offline=True)
    assert r["degraded"] == ["sentiment"]
    assert "kaput" in r["agents"][1]["error"]
    assert r["rating"] is not None  # brief still produced from remaining agents
    assert set(r["agents"][3]["data"]["weights"]) == {"fundamentals", "technicals"}


def test_market_failure_raises_clear_error(monkeypatch):
    def boom(*a, **k):
        raise graph.data.DataError("no network")
    monkeypatch.setattr(graph.data, "get_market", boom)
    with pytest.raises(graph.data.DataError, match="no network"):
        graph.research("AAPL", offline=True)


def test_missing_news_degrades_sentiment_only(monkeypatch):
    def boom(*a, **k):
        raise graph.data.DataError("news down")
    monkeypatch.setattr(graph.data, "get_news", boom)
    r = graph.research("AAPL", offline=True)
    assert r["degraded"] == ["sentiment"] and r["rating"] is not None


def test_graph_rejects_bad_ticker():
    with pytest.raises(graph.data.DataError):
        graph.research("not a ticker!", offline=True)


# ---- API
@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "get_settings", lambda: Settings(db_path=str(tmp_path / "t.db")))
    monkeypatch.setattr(main, "get_settings", lambda: Settings(db_path=str(tmp_path / "t.db")))
    return TestClient(main.app)


def test_health(client):
    j = client.get("/api/health").json()
    assert j["status"] == "ok" and "AAPL" in j["offline_tickers"]


def test_research_save_and_fetch(client):
    r = client.post("/api/research", json={"ticker": "aapl", "mode": "offline"})
    assert r.status_code == 200
    rid = r.json()["id"]
    assert client.get(f"/api/reports/{rid}").json()["ticker"] == "AAPL"
    assert client.get("/api/reports").json()[0]["id"] == rid
    assert client.get("/api/reports/9999").status_code == 404


def test_research_validation_errors(client):
    assert client.post("/api/research", json={"ticker": ""}).status_code == 422
    assert client.post("/api/research", json={"ticker": "ZZZZ", "mode": "offline"}).status_code == 400
    assert client.post("/api/research", json={"ticker": "AAPL", "mode": "weird"}).status_code == 422


def test_llm_provider_misconfigured_is_400(client, monkeypatch):
    def bad():
        raise LLMError("OPENAI_API_KEY is not set")
    monkeypatch.setattr(main, "get_client", bad)
    r = client.post("/api/research", json={"ticker": "AAPL", "use_llm": True})
    assert r.status_code == 400 and "OPENAI_API_KEY" in r.json()["detail"]


def test_token_auth(tmp_path, monkeypatch):
    s = Settings(db_path=str(tmp_path / "a.db"), api_token="s3cret")
    monkeypatch.setattr(main, "get_settings", lambda: s)
    monkeypatch.setattr(store, "get_settings", lambda: s)
    c = TestClient(main.app)
    body = {"ticker": "AAPL"}
    assert c.post("/api/research", json=body).status_code == 401
    assert c.post("/api/research", json=body, headers={"Authorization": "Bearer nope"}).status_code == 401
    assert c.get("/api/reports").status_code == 401
    assert c.post("/api/research", json=body, headers={"Authorization": "Bearer s3cret"}).status_code == 200
    assert c.get("/api/health").status_code == 200  # health stays open
