# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot that monitors rutor.info for new torrents and manages downloads via qBittorrent. The bot uses multiprocessing to run the Telegram bot and scheduler in separate processes.

## Development Commands

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Create a new migration after model changes
uv run alembic revision --autogenerate -m "Description of changes"

# Run the bot locally
uv run telegram-rutor-bot bot      # Run Telegram bot
uv run telegram-rutor-bot scheduler # Run TaskIQ scheduler
uv run telegram-rutor-bot worker   # Run TaskIQ worker

# Run with Docker Compose (recommended for production)
docker-compose up -d               # Start all services
docker-compose logs -f             # View logs
docker-compose down                # Stop all services

# Hybrid Development (Frontend + Backend)
# 1. Start Infra (Postgres:5433, Redis:6380, QB:8090)
docker compose up -d postgres redis qbittorrent

# 2. Run Backend (Host 0.0.0.0, Port 8088)
# Export RUTOR_BOT_DATABASE_URL=postgresql://rutor:rutorpass@localhost:5433/rutorbot
# Export RUTOR_BOT_REDIS_URL=redis://localhost:6380/0
uv run uvicorn src.telegram_rutor_bot.web.app:app --reload --port 8088 --host 0.0.0.0

# 3. Run Frontend
cd frontend && npm run dev
```

## Architecture

### Project Structure

The project uses a standard Python package structure with all source code in `src/telegram_rutor_bot/`:

```
src/telegram_rutor_bot/
├── main.py              # Entry point using multiprocessing
├── config.py            # Pydantic settings configuration
├── db/                  # Database layer with SQLAlchemy
│   ├── models.py        # SQLAlchemy ORM models
│   ├── database.py      # Database connection and session management
│   ├── migrate.py       # Alembic migration utilities
│   └── [operation files] # CRUD operations for each model
├── handlers/            # Telegram command handlers
├── rutor/              # Web scraper for rutor.info
├── tasks/              # TaskIQ jobs and broker configuration
│   ├── broker.py       # TaskIQ broker setup (Redis/InMemory)
│   └── jobs.py         # Scheduled tasks
└── utils/              # Utilities (security, etc.)
```

### Core Components

1. **main.py**: Entry point with three modes: bot, scheduler, worker
2. **handlers/**: Telegram command handlers (search, subscribe, torrents, commons)
3. **db/**: SQLAlchemy-based database layer with Alembic migrations
4. **rutor/parser.py**: Web scraper for rutor.info with Transmission integration
5. **tasks/**: TaskIQ-based job scheduling and execution
6. **utils/security.py**: Decorator-based authorization using user whitelist

### Key Design Patterns

- **Microservices**: Bot, scheduler, and worker run as separate services
- **Message Queue**: TaskIQ with Redis for distributed task processing
- **Context Managers**: Database connections handled via `with` statements
- **Decorators**: `@is_allowed` security decorator on all bot commands
- **Dynamic Commands**: Commands like `/dl_{id}` are parsed from message text

### Database Schema (SQLAlchemy with Alembic)

- **films**: Movie information (id, blake, year, name, ru_name, poster, rating)
- **torrents**: Torrent data (id, film_id, blake, name, magnet, created, link, sz, approved, downloaded, seeds, date)
- **users**: Telegram users (id, chat_id, name, username)
- **searches**: User search queries (id, url, cron, last_success, creator_id, query)
- **subscribes**: User subscriptions to searches (search_id, user_id)

Database migrations are managed with Alembic. Run `uv run alembic upgrade head` to apply migrations.

### Configuration

Configuration uses pydantic-settings with TOML format. Create `config.toml` from `config.toml.example`:

- `telegram_token`: Bot API token
- `qbittorrent_host`, `qbittorrent_port`, `qbittorrent_username`, `qbittorrent_password`: qBittorrent settings
- `proxy`: Optional proxy for accessing rutor.info
- `database_path`: Database file path
- `redis_url`: Optional Redis URL for multi-container setup (defaults to InMemoryBroker)

Configuration can also be set via environment variables with prefix `RUTOR_BOT_`.

### Important Considerations

1. **Security**: All commands require user ID in ALLOWED_IDS list
2. **Date Parsing**: rutor.info dates are parsed with Russian locale
3. **Torrent IDs**: Dynamic commands extract IDs from command text (e.g., `/dl_123`)
4. **Task Queue**: TaskIQ handles scheduled searches and notifications
5. **Error Handling**: Parser includes retry logic with proxy support
6. **Multi-container**: Use Redis for production, InMemoryBroker for development
