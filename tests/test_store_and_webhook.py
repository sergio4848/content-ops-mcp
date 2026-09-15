import datetime as dt
import json

import httpx
import pytest

from content_ops import webhook
from content_ops.store import ContentStore


@pytest.fixture
def store():
    return ContentStore(":memory:")


def test_add_and_get(store):
    item = store.add("Derby matchday teaser", "Instagram", "2026-09-20", format="Reel")
    assert item["id"] == 1
    assert item["channel"] == "instagram"
    assert item["format"] == "reel"
    assert item["status"] == "idea"
    assert store.get(1)["title"] == "Derby matchday teaser"


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"title": " ", "channel": "x", "publish_date": "2026-09-20"}, "Title"),
        ({"title": "Post", "channel": "x", "publish_date": "20-09-2026"}, "Invalid date"),
        ({"title": "Post", "channel": "x", "publish_date": "2026-09-20", "status": "live"}, "Invalid status"),
    ],
)
def test_add_validation(store, kwargs, error):
    with pytest.raises(ValueError, match=error):
        store.add(**kwargs)


def test_list_filters(store):
    store.add("A", "tiktok", "2026-09-18")
    store.add("B", "instagram", "2026-09-25", status="draft")
    store.add("C", "instagram", "2026-10-02")
    assert [i["title"] for i in store.list(channel="Instagram")] == ["B", "C"]
    assert [i["title"] for i in store.list(status="draft")] == ["B"]
    assert [i["title"] for i in store.list(date_from="2026-09-20", date_to="2026-09-30")] == ["B"]


def test_set_status_and_missing_item(store):
    store.add("A", "youtube", "2026-09-18")
    assert store.set_status(1, "scheduled")["status"] == "scheduled"
    with pytest.raises(ValueError, match="not found"):
        store.set_status(99, "draft")


def test_upcoming_skips_published_and_far_items(store):
    today = dt.date(2026, 9, 15)
    store.add("Soon", "x", "2026-09-17")
    store.add("Done", "x", "2026-09-16", status="published")
    store.add("Later", "x", "2026-10-30")
    assert [i["title"] for i in store.upcoming(days=14, today=today)] == ["Soon"]


def test_build_payload_contains_summary():
    item = {"title": "Teaser", "channel": "tiktok", "publish_date": "2026-09-20", "status": "scheduled"}
    payload = webhook.build_payload(item, "Assets ready")
    assert payload["text"].startswith("[scheduled] Teaser - tiktok on 2026-09-20")
    assert "Assets ready" in payload["text"]
    assert payload["item"] == item


async def test_send_posts_json():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        return httpx.Response(204)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        code = await webhook.send("https://hooks.example.test/abc", {"text": "hi"}, client=client)
    assert code == 204
    assert seen == {"url": "https://hooks.example.test/abc", "body": {"text": "hi"}}


async def test_send_requires_url_and_raises_on_error():
    with pytest.raises(ValueError, match="not configured"):
        await webhook.send("", {"text": "hi"})
    transport = httpx.MockTransport(lambda request: httpx.Response(500))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await webhook.send("https://hooks.example.test/abc", {"text": "hi"}, client=client)
