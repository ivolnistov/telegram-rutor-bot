#!/bin/bash
# Single-container run script using supervisor-like approach
# This script runs all components in a single process using Python multiprocessing

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Sync dependencies
echo "Syncing dependencies..."
uv sync

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Run migrations
echo "Running database migrations..."
uv run alembic upgrade head

# Check if config exists
if [ ! -f "config.toml" ]; then
    if [ -f "config.toml.example" ]; then
        echo "Warning: config.toml not found. Creating from example..."
        cp config.toml.example config.toml
        echo "Please edit config.toml with your settings"
        exit 1
    else
        echo "Error: config.toml not found"
        exit 1
    fi
fi

# Start all services in single process
echo "Starting Telegram Rutor Bot (single-container mode)..."
echo "Using SQLite database and in-memory task broker"
echo ""

# Run the main application which handles all components
# Start API in background
echo "Starting API..."
uv run uvicorn telegram_rutor_bot.web.app:app --host 0.0.0.0 --port 8088 &
API_PID=$!

# Start Bot in background
echo "Starting Bot..."
uv run python -m telegram_rutor_bot.main bot &
BOT_PID=$!

# Start Scheduler in background
echo "Starting Scheduler..."
uv run python -m telegram_rutor_bot.main scheduler &
SCHEDULER_PID=$!

# Start Worker in background
echo "Starting Worker..."
uv run python -m telegram_rutor_bot.main worker &
WORKER_PID=$!

# Clean up function
cleanup() {
    echo "Stopping all services..."
    kill $API_PID $BOT_PID $SCHEDULER_PID $WORKER_PID 2>/dev/null
    exit
}

# Trap signals
trap cleanup SIGINT SIGTERM

echo "All services started. Press Ctrl+C to stop."
wait
