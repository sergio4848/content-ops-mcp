"""MCP server that lets an LLM client manage a social media content calendar.

Tools: add_content_item, list_content_items, update_status, notify_webhook
Resource: calendar://upcoming
Run:  python server.py            (stdio transport, for Claude Desktop / MCP clients)
      mcp dev server.py           (MCP Inspector)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from content_ops import webhook
from content_ops.store import ContentStore

DB_PATH = os.environ.get("CONTENT_OPS_DB", str(Path(__file__).with_name("content_ops.db")))
WEBHOOK_URL = os.environ.get("CONTENT_OPS_WEBHOOK_URL", "")

store = ContentStore(DB_PATH)
mcp = MCPServer("content-ops")


def _checked(fn, *args, **kwargs):
    """Turn validation errors into tool errors so the LLM sees the reason and can retry."""
    try:
        return fn(*args, **kwargs)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def add_content_item(
    title: str,
    channel: str,
    publish_date: str,
    format: str = "post",
    notes: str = "",
) -> dict:
    """Add a content idea to the calendar.

    Args:
        title: Working title of the post or video.
        channel: Platform, e.g. instagram, tiktok, youtube, x, linkedin.
        publish_date: Planned publish date as YYYY-MM-DD.
        format: post, reel, story, short, video or thread.
        notes: Optional brief, hook or asset notes.
    """
    return _checked(store.add, title, channel, publish_date, format=format, notes=notes)


@mcp.tool()
def list_content_items(
    status: str | None = None,
    channel: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """List calendar items, optionally filtered by status, channel and date range (YYYY-MM-DD)."""
    return _checked(store.list, status=status, channel=channel, date_from=date_from, date_to=date_to)


@mcp.tool()
def update_status(item_id: int, status: str) -> dict:
    """Move an item through the workflow. Allowed statuses: idea, draft, scheduled, published."""
    return _checked(store.set_status, item_id, status)


@mcp.tool()
async def notify_webhook(item_id: int, message: str = "") -> str:
    """Send a calendar item to the configured webhook (e.g. a Slack or Discord channel)."""
    item = _checked(store.get, item_id)
    try:
        status_code = await webhook.send(WEBHOOK_URL, webhook.build_payload(item, message))
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise ToolError(f"Webhook request failed: {exc}") from exc
    return f"Webhook delivered for item {item_id} (HTTP {status_code})"


@mcp.resource("calendar://upcoming")
def upcoming_calendar() -> str:
    """Unpublished items planned for the next 14 days, as JSON."""
    return json.dumps(store.upcoming(days=14), indent=2)


if __name__ == "__main__":
    mcp.run()
