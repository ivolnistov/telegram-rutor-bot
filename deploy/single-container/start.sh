#!/bin/sh
set -e

uv run alembic upgrade head
exec uv run python -m telegram_rutor_bot.main
