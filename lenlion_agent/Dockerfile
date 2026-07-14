# syntax=docker/dockerfile:1
#
# Lenlion Agent — slim Docker image (adapted from upstream Hermes, minus the
# s6-overlay / ui-tui / desktop machinery this fork removed).
#
# Two long-running services share this one image (see docker-compose.yml):
#   - dashboard : Vue Web Chat + FastAPI  (lenlion dashboard)
#   - gateway   : messaging gateway       (lenlion gateway run)
# Both read/write user state under /data (HERMES_HOME).

# ---------- Stage 1: build the Vue Web UI ----------
FROM node:22-bookworm-slim AS web-builder
WORKDIR /src
# Cache npm install on lockfiles only.
COPY web/package.json web/package-lock.json web/
RUN cd web && npm ci
COPY web/ web/
# vite outDir is ../hermes_cli/web_dist (see web/vite.config.ts), so the build
# emits to /src/hermes_cli/web_dist.
RUN cd web && npm run build

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HERMES_HOME=/data \
    HERMES_WRITE_SAFE_ROOT=/data \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/opt/lenlion/.venv/bin:${PATH}"

# Tools the agent shells out to: ripgrep, git, curl. ffmpeg omitted from the
# default image to keep apt lean (add in a derived image if media tools need it).
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git ripgrep \
    && rm -rf /var/lib/apt/lists/*

# uv (pinned, same major as upstream uses).
COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /usr/local/bin/

WORKDIR /opt/lenlion

# ---- Dependency layer (cached unless pyproject.toml / uv.lock change) ----
# README.md is referenced by pyproject's `readme =`, so it must be present
# for the build frontend to resolve metadata.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project \
        --extra cli --extra web --extra mcp --extra cron \
        --extra messaging --extra anthropic --extra postgres

# ---- App source + prebuilt web dist ----
COPY . .
COPY --from=web-builder /src/hermes_cli/web_dist ./hermes_cli/web_dist
# Editable link only (deps already installed above) — fast, no network.
RUN uv pip install --no-deps -e .

# ---- Non-root runtime; /data is the only writable surface ----
RUN useradd -u 10001 -m -d /data lenlion \
    && mkdir -p /data \
    && chown -R lenlion:lenlion /data
USER lenlion
VOLUME ["/data"]

EXPOSE 9119
ENTRYPOINT ["lenlion"]
# Default service = dashboard. --skip-build serves the baked dist (no npm at
# runtime); --insecure is required to bind beyond localhost INSIDE the container
# (host exposure is still gated by the compose `ports:` loopback mapping).
CMD ["dashboard", "--host", "0.0.0.0", "--port", "9119", "--no-open", "--skip-build", "--insecure"]
