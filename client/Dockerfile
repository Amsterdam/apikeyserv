FROM ghcr.io/astral-sh/uv:0.13-python3.14-trixie-slim AS builder
MAINTAINER datapunt@amsterdam.nl

# Configure uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Install production dependencies
RUN uv sync --locked --no-dev --no-install-project

# Start runtime image.
FROM python:3.14-slim-trixie

RUN useradd -M -U datapunt

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

COPY . ./

EXPOSE 8000
USER datapunt
CMD ["python", "__init__.py", "runserver", "0.0.0.0:8000"]
