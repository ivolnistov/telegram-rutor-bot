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
exec uv run python -m telegram_rutor_bot.main
