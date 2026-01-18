# Single-container Dockerfile for Telegram Rutor Bot
# This version includes everything needed to run the bot in a single container
# with SQLite database and in-memory task broker

FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .

# Copy source code (needed for package installation)
COPY src/ src/

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy remaining files
COPY alembic.ini .
COPY alembic/ alembic/

# Create directory for data persistence
RUN mkdir -p /app/data

# Environment variables with defaults for single-container mode
ENV RUTOR_BOT_DATABASE_PATH=/app/data/rutor.db \
    RUTOR_BOT_REDIS_URL="" \
    RUTOR_BOT_LOG_LEVEL=INFO

# Volume for persistent data
VOLUME ["/app/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD uv run python -c "import sys; from pathlib import Path; sys.exit(0 if Path('/app/data/rutor.db').exists() else 1)"

# Run migrations and start all services using supervisor
CMD uv run alembic upgrade head && \
    uv run python -m telegram_rutor_bot.main
