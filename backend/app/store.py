import json
import sqlite3
from contextlib import closing

from .config import get_settings

SCHEMA = """CREATE TABLE IF NOT EXISTS reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT NOT NULL, created_at TEXT NOT NULL,
  rating TEXT, score REAL, mode TEXT, body TEXT NOT NULL)"""


def _conn(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or get_settings().db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def save(report: dict, path: str | None = None) -> int:
    with closing(_conn(path)) as c, c:
        cur = c.execute(
            "INSERT INTO reports (ticker, created_at, rating, score, mode, body) VALUES (?,?,?,?,?,?)",
            (report["ticker"], report["created_at"], report.get("rating"), report.get("score"), report["mode"], json.dumps(report)),
        )
        return cur.lastrowid


def list_reports(limit: int = 50, path: str | None = None) -> list[dict]:
    with closing(_conn(path)) as c:
        rows = c.execute("SELECT id, ticker, created_at, rating, score, mode FROM reports ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def get(report_id: int, path: str | None = None) -> dict | None:
    with closing(_conn(path)) as c:
        row = c.execute("SELECT id, body FROM reports WHERE id = ?", (report_id,)).fetchone()
    return {"id": row["id"], **json.loads(row["body"])} if row else None
