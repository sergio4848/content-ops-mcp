# Content Ops MCP

An MCP (Model Context Protocol) server that gives an LLM client, such as Claude Desktop, real tools for a social media content calendar. The client can plan posts, move them through a workflow and push updates to a team channel through a webhook.

It shows the pattern of connecting an LLM to external data and services through MCP instead of prompt-only use:

- **Data source:** a SQLite content calendar (`content_ops/store.py`)
- **External service:** outgoing JSON webhooks, compatible with Slack/Discord-style incoming webhooks (`content_ops/webhook.py`)
- **MCP layer:** tools and a resource built with the official Python MCP SDK (`server.py`)

## Tools and resources

| Name | Type | What it does |
|------|------|--------------|
| `add_content_item` | tool | Adds a post/video idea with channel, format and publish date |
| `list_content_items` | tool | Lists items filtered by status, channel and date range |
| `update_status` | tool | Moves an item through `idea → draft → scheduled → published` |
| `notify_webhook` | tool | Sends an item summary to the configured webhook |
| `calendar://upcoming` | resource | Unpublished items planned for the next 14 days (JSON) |

## Setup

Requires Python 3.10+ and the MCP Python SDK 2.x (`MCPServer`).

```bash
python -m venv .venv
.venv/Scripts/python -m pip install "mcp[cli]>=2.2,<3" httpx pytest pytest-asyncio   # Windows
# source .venv/bin/activate && pip install "mcp[cli]>=2.2,<3" httpx pytest pytest-asyncio   # macOS/Linux
```

Optional environment variables:

- `CONTENT_OPS_DB`: SQLite file path (default: `content_ops.db` next to `server.py`)
- `CONTENT_OPS_WEBHOOK_URL`: incoming webhook URL for `notify_webhook`

## Run

```bash
.venv/Scripts/python server.py        # stdio transport
.venv/Scripts/mcp dev server.py       # test the tools in MCP Inspector
.venv/Scripts/python -m pytest        # unit tests
```

### Claude Desktop

Add to `claude_desktop_config.json` (adjust the paths):

```json
{
  "mcpServers": {
    "content-ops": {
      "command": "C:/path/to/content-ops-mcp/.venv/Scripts/python.exe",
      "args": ["C:/path/to/content-ops-mcp/server.py"],
      "env": { "CONTENT_OPS_WEBHOOK_URL": "https://hooks.slack.com/services/..." }
    }
  }
}
```

Example prompts: *"Plan three Instagram reels for next week's derby and add them to the calendar"*, *"What is still unpublished for the next 14 days?"*, *"Mark item 2 as scheduled and notify the team."*

### Docker

```bash
docker build -t content-ops-mcp .
docker run -i --rm -v content-ops-data:/data -e CONTENT_OPS_WEBHOOK_URL=... content-ops-mcp
```

## Notes

Portfolio/demo project by Sergen Şahin. It is a demo, not a production system.
