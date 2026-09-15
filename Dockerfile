FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir "mcp[cli]>=2.2,<3" "httpx>=0.27"
COPY content_ops ./content_ops
COPY server.py ./

ENV CONTENT_OPS_DB=/data/content_ops.db
VOLUME ["/data"]

# stdio transport: run with `docker run -i --rm -v content-ops-data:/data content-ops-mcp`
CMD ["python", "server.py"]
