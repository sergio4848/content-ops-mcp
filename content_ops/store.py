"""SQLite-backed content calendar used by the MCP server."""

from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

STATUSES = ("idea", "draft", "scheduled", "published")

SCHEMA = """
CREATE TABLE IF NOT EXISTS content_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    channel TEXT NOT NULL,
    format TEXT NOT NULL DEFAULT 'post',
    publish_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'idea',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _check_date(value: str) -> str:
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}', expected YYYY-MM-DD") from exc


def _check_status(value: str) -> str:
    if value not in STATUSES:
        raise ValueError(f"Invalid status '{value}', expected one of {', '.join(STATUSES)}")
    return value


class ContentStore:
    """Small data-access layer for content calendar items."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(SCHEMA)
        self.conn.commit()

    def add(
        self,
        title: str,
        channel: str,
        publish_date: str,
        format: str = "post",
        notes: str = "",
        status: str = "idea",
    ) -> dict:
        if not title.strip():
            raise ValueError("Title must not be empty")
        if not channel.strip():
            raise ValueError("Channel must not be empty")
        now = _now()
        cur = self.conn.execute(
            "INSERT INTO content_items (title, channel, format, publish_date, status, notes, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (title.strip(), channel.strip().lower(), format.strip().lower(), _check_date(publish_date),
             _check_status(status), notes, now, now),
        )
        self.conn.commit()
        return self.get(cur.lastrowid)

    def get(self, item_id: int) -> dict:
        row = self.conn.execute("SELECT * FROM content_items WHERE id = ?", (item_id,)).fetchone()
        if row is None:
            raise ValueError(f"Content item {item_id} not found")
        return dict(row)

    def list(
        self,
        status: str | None = None,
        channel: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        clauses, params = [], []
        if status:
            clauses.append("status = ?")
            params.append(_check_status(status))
        if channel:
            clauses.append("channel = ?")
            params.append(channel.strip().lower())
        if date_from:
            clauses.append("publish_date >= ?")
            params.append(_check_date(date_from))
        if date_to:
            clauses.append("publish_date <= ?")
            params.append(_check_date(date_to))
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self.conn.execute(
            f"SELECT * FROM content_items{where} ORDER BY publish_date, id", params
        ).fetchall()
        return [dict(r) for r in rows]

    def set_status(self, item_id: int, status: str) -> dict:
        self.get(item_id)
        self.conn.execute(
            "UPDATE content_items SET status = ?, updated_at = ? WHERE id = ?",
            (_check_status(status), _now(), item_id),
        )
        self.conn.commit()
        return self.get(item_id)

    def upcoming(self, days: int = 14, today: dt.date | None = None) -> list[dict]:
        start = today or dt.date.today()
        end = start + dt.timedelta(days=days)
        return [
            item
            for item in self.list(date_from=start.isoformat(), date_to=end.isoformat())
            if item["status"] != "published"
        ]
