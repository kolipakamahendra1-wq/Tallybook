import hmac
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import data, store
from .config import get_settings
from .graph import research
from .llm import LLMError, get_client

app = FastAPI(title="AI Stock Research", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def require_token(authorization: str | None = Header(default=None)) -> None:
    token = get_settings().api_token
    if not token:
        return  # auth disabled for local use; documented in README
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    if not hmac.compare_digest(supplied, token):
        raise HTTPException(401, "missing or invalid API token")


class ResearchRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=10)
    mode: Literal["offline", "live"] = "offline"
    use_llm: bool = False


@app.get("/api/health")
def health():
    s = get_settings()
    return {"status": "ok", "llm_provider": s.llm_provider, "auth_required": bool(s.api_token), "offline_tickers": data.fixture_tickers()}


@app.post("/api/research", dependencies=[Depends(require_token)])
def run_research(req: ResearchRequest):
    llm = None
    if req.use_llm:
        try:
            llm = get_client()
        except LLMError as exc:
            raise HTTPException(400, str(exc)) from exc
    try:
        report = research(req.ticker, offline=req.mode == "offline", llm=llm)
    except data.DataError as exc:
        raise HTTPException(400, str(exc)) from exc
    report["id"] = store.save(report)
    return report


@app.get("/api/reports", dependencies=[Depends(require_token)])
def reports(limit: int = 50):
    return store.list_reports(max(1, min(limit, 200)))


@app.get("/api/reports/{report_id}", dependencies=[Depends(require_token)])
def report(report_id: int):
    found = store.get(report_id)
    if not found:
        raise HTTPException(404, "report not found")
    return found
