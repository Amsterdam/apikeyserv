FROM ghcr.io/astral-sh/uv:0.13-python3.14-trixie-slim AS builder
MAINTAINER datapunt@amsterdam.nl

# Configure uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Install production dependencies
RUN uv sync --locked --no-dev --no-install-project

# Start runtime image.
FROM python:3.14-slim-trixie

RUN useradd -M -U datapunt

# Install libexpat1 for uwsgi
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application
COPY . ./


ENV DJANGO_SETTINGS_MODULE=apikeyserv.settings
RUN mkdir /static && chown datapunt:datapunt /static

RUN python manage.py collectstatic --noinput

EXPOSE 8000
USER datapunt
CMD ["uwsgi"]
