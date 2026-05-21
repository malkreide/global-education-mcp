# syntax=docker/dockerfile:1.7
# Multi-stage Build fuer global-education-mcp.
# Adressiert Audit-Finding SEC-007 (Container-Sandboxing):
#   - non-root User (uid 10001) in der Runtime-Stage
#   - keine Build-Tools im finalen Image
#   - explizite PORT/HOST-Defaults, MCP_HOST=0.0.0.0 (Container-only)
#
# Empfohlene Runtime-Flags (siehe docker-compose.yml):
#   --read-only --cap-drop ALL --security-opt no-new-privileges

ARG PYTHON_VERSION=3.13

# ─── Build-Stage ──────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Wheel bauen und in /wheels ablegen. Die runtime-stage installiert nur
# das fertige Wheel + transitive Deps via pip, ohne Build-Toolchain im Image.
RUN pip install --upgrade pip build && \
    python -m build --wheel --outdir /wheels

# ─── Runtime-Stage ────────────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    MCP_TRANSPORT=sse \
    MCP_HOST=0.0.0.0 \
    PORT=8000

# Non-root User (uid 10001 ist ausserhalb der Distribution-Reserved-Range).
RUN groupadd --system --gid 10001 mcp && \
    useradd --system --uid 10001 --gid mcp --home-dir /home/mcp \
            --create-home --shell /usr/sbin/nologin mcp

COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/global_education_mcp-*.whl && \
    rm -rf /wheels

USER mcp
WORKDIR /home/mcp
EXPOSE 8000

# stdio-Mode ist ueber Container wenig sinnvoll; default = sse.
ENTRYPOINT ["global-education-mcp"]
