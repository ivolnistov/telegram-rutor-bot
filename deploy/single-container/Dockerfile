# Single-container Dockerfile for Telegram Rutor Bot
# This version includes everything needed to run the bot in a single container
# with SQLite database and in-memory task broker

FROM python:3.14-slim

# Install system dependencies and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:$PATH"

# Create app directory
RUN useradd -m rutor
WORKDIR /app
RUN chown rutor:rutor /app

# Copy dependency files
COPY --chown=rutor:rutor pyproject.toml .
COPY --chown=rutor:rutor uv.lock .
COPY --chown=rutor:rutor README.md .

# Copy source code (needed for package installation)
COPY --chown=rutor:rutor src/ src/

# Copy start script
COPY --chown=rutor:rutor deploy/single-container/start.sh .
RUN chmod +x start.sh

USER rutor
ENV PATH="/home/rutor/.local/bin:$PATH"

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy remaining files
COPY --chown=rutor:rutor alembic.ini .
COPY --chown=rutor:rutor alembic/ alembic/

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
CMD ["./start.sh"]
