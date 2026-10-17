FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Build context is the repo root (uv workspace)
COPY . .
RUN uv sync --no-dev --package hookd-mcp

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8001
CMD ["hookd-mcp"]
