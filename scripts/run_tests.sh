#!/bin/bash

echo "Running telegram-rutor-bot tests..."

# Install test dependencies if needed
echo "Installing test dependencies..."
uv sync --dev

# Run different test suites
echo -e "\n=== Running unit tests ==="
uv run pytest tests/unit -v -m "unit"

echo -e "\n=== Running integration tests (without external) ==="
uv run pytest tests/integration -v -m "integration and not external"

# Check if we should run external tests
if [ "$1" == "--external" ]; then
    echo -e "\n=== Running external integration tests ==="
    echo "WARNING: These tests will connect to real websites (rutor.info, imdb.com, kinopoisk.ru)"
    uv run pytest tests/integration -v -m "external" --run-external
fi

# Generate coverage report
echo -e "\n=== Coverage report ==="
uv run pytest --cov=src/telegram_rutor_bot --cov-report=term-missing --cov-report=html

echo -e "\nDone! Coverage report available in htmlcov/index.html"
