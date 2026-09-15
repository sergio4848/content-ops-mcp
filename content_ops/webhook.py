"""Outgoing webhook notifications for content calendar events."""

from __future__ import annotations

import httpx


def build_payload(item: dict, message: str = "") -> dict:
    """JSON body sent to the webhook (works with Slack/Discord-style incoming webhooks)."""
    summary = f"[{item['status']}] {item['title']} - {item['channel']} on {item['publish_date']}"
    text = f"{summary}\n{message}" if message else summary
    return {"text": text, "content": text, "item": item}


async def send(url: str, payload: dict, client: httpx.AsyncClient | None = None) -> int:
    """POST the payload and return the HTTP status code; raises on 4xx/5xx."""
    if not url:
        raise ValueError("Webhook URL is not configured (set CONTENT_OPS_WEBHOOK_URL)")
    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=10)
    try:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.status_code
    finally:
        if owns_client:
            await client.aclose()
