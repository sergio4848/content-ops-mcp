import os

os.environ["CONTENT_OPS_DB"] = ":memory:"
os.environ["CONTENT_OPS_WEBHOOK_URL"] = ""

import pytest  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

import server  # noqa: E402


def test_tools_return_items_and_map_validation_errors():
    item = server.add_content_item("Derby teaser", "tiktok", "2026-09-20", format="short")
    assert server.update_status(item["id"], "draft")["status"] == "draft"
    with pytest.raises(ToolError, match="Invalid status 'live'"):
        server.update_status(item["id"], "live")
    with pytest.raises(ToolError, match="Invalid date"):
        server.add_content_item("Bad date", "x", "20/09/2026")


async def test_notify_webhook_without_url_is_tool_error():
    item = server.add_content_item("Kit launch", "instagram", "2026-09-22")
    with pytest.raises(ToolError, match="not configured"):
        await server.notify_webhook(item["id"])
