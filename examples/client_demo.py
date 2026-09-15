"""End-to-end demo: start server.py over stdio and call its tools as an MCP client would.

Run from the project root:  .venv/Scripts/python examples/client_demo.py
Uses a temporary database, so it never touches content_ops.db.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent


def show(label, result):
    text = " ".join(getattr(c, "text", str(c)) for c in result.content).replace("\n", " ")
    print(f"{label} -> is_error={result.is_error} | {text[:200]}")


async def main():
    env = dict(os.environ, CONTENT_OPS_DB=os.path.join(tempfile.mkdtemp(), "demo.db"))
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "server.py")], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("tools:", [t.name for t in (await session.list_tools()).tools])
            show("add", await session.call_tool(
                "add_content_item",
                {"title": "Derby matchday teaser", "channel": "Instagram", "publish_date": "2026-09-20", "format": "reel"},
            ))
            show("update", await session.call_tool("update_status", {"item_id": 1, "status": "scheduled"}))
            show("list", await session.call_tool("list_content_items", {"channel": "instagram"}))
            upcoming = await session.read_resource("calendar://upcoming")
            print("calendar://upcoming ->", upcoming.contents[0].text[:200].replace("\n", " "))


if __name__ == "__main__":
    asyncio.run(main())
