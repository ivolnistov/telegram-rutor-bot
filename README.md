# Telegram Rutor Bot

A Telegram bot for monitoring and downloading torrents from rutor.info with support for Transmission and qBittorrent.

## Features

- 🔍 Monitor rutor.info for new torrents
- 📥 Automatic downloads via Transmission or qBittorrent
- 🔔 Search subscriptions with notifications
- 🎬 Extract movie information with posters
- 👥 Multi-user support with whitelist authorization
- 🐳 Docker and Docker Compose deployment
- 📊 PostgreSQL for production, SQLite for development
- ⚡ Async architecture with TaskIQ for distributed task processing
- 🔄 Database migrations via Alembic

## Quick Start

### Using Docker (Recommended)

#### Option 1: Single Container (Simple)

Perfect for personal use or small deployments:

```bash
# Clone and configure
git clone https://github.com/yourusername/telegram-rutor-bot.git
cd telegram-rutor-bot
cp .env.example .env
# Edit .env with your settings

# Run single container
docker-compose -f docker-compose.single.yml up -d
```

#### Option 2: Multi-Container (Production)

For high-availability production deployments:

```bash
# Clone and configure
git clone https://github.com/yourusername/telegram-rutor-bot.git
cd telegram-rutor-bot
cp config.toml.example config.toml
# Edit config.toml with your settings

# Run full stack
docker-compose up -d
```

### Local Development

1. Install dependencies:
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

2. Apply database migrations:
```bash
uv run alembic upgrade head
```

3. Run the bot:
```bash
uv run python -m telegram_rutor_bot
```

## Bot Commands

- `/start` - Start bot interaction
- `/search <query>` - Search for torrents
- `/dl_<id>` - Download torrent
- `/in_<id>` - Get torrent info with images
- `/list` - List recent torrents
- `/add_search <url> <cron>` - Add search subscription (e.g., `/add_search http://rutor.info/search/0/0/100/0/matrix * * * * *`)
- `/list_search` - Show all your searches
- `/list_subscriptions` - Show your active subscriptions
- `/subscribe_<id>` - Subscribe to search notifications
- `/unsubscribe_<id>` - Unsubscribe from notifications
- `/ds_<id>` - Delete search
- `/es_<id>` - Execute search now

## Configuration

### Main Settings

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `telegram_token` | Telegram bot token | Yes | - |
| `users_white_list` | List of allowed Telegram IDs | Yes | [] |
| `torrent_client` | Torrent client (transmission/qbittorrent) | No | transmission |
| `proxy` | Proxy for accessing rutor.info | No | - |
| `log_level` | Logging level | No | INFO |
| `database_path` | SQLite database path | No | var/rutor.db |
| `database_url` | PostgreSQL URL | No | - |

### Environment Variables

All settings can be configured via environment variables with `RUTOR_BOT_` prefix:

```bash
RUTOR_BOT_TELEGRAM_TOKEN=your-token
RUTOR_BOT_USERS_WHITE_LIST=[123456789]
RUTOR_BOT_TORRENT_CLIENT=qbittorrent
RUTOR_BOT_PROXY=socks5://localhost:1080
```

## Documentation

- [Installation Guide](docs/installation.md) - Detailed installation instructions
- [Configuration Guide](docs/configuration.md) - All configuration options explained
- [Deployment Guide](docs/deployment.md) - Production deployment strategies
- [Torrent Clients](docs/torrent-clients.md) - Setting up Transmission and qBittorrent
- [API Reference](docs/api.md) - Bot commands and API documentation

## Quick Deployment

### Production with PostgreSQL and Redis

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database
- Redis for task queue
- Bot service
- TaskIQ scheduler
- TaskIQ workers

### Single Container Deployment

For simple deployments without external dependencies:

```bash
# Using Docker Compose
docker-compose -f docker-compose.single.yml up -d

# Or build and run manually
docker build -f Dockerfile.single -t telegram-rutor-bot:single .
docker run -d --name telegram-rutor-bot \
  -e RUTOR_BOT_TELEGRAM_TOKEN=your-token \
  -e RUTOR_BOT_USERS_WHITE_LIST=123456789 \
  -v bot-data:/app/data \
  telegram-rutor-bot:single
```

See [Single Container Guide](docs/single-container.md) for details.

### Adding Torrent Client to Docker Compose

#### Transmission Example

```yaml
transmission:
  image: linuxserver/transmission
  environment:
    - PUID=1000
    - PGID=1000
    - USER=admin
    - PASS=password
  volumes:
    - ./transmission/config:/config
    - ./downloads:/downloads
  ports:
    - 9091:9091
```

#### qBittorrent Example

```yaml
qbittorrent:
  image: linuxserver/qbittorrent
  environment:
    - PUID=1000
    - PGID=1000
    - WEBUI_PORT=8080
  volumes:
    - ./qbittorrent/config:/config
    - ./downloads:/downloads
  ports:
    - 8080:8080
```

## Architecture

### Project Structure

```
telegram-rutor-bot/
├── src/telegram_rutor_bot/
│   ├── config.py           # Configuration management
│   ├── main.py            # Entry point
│   ├── bot.py             # Telegram bot setup
│   ├── db/                # Database models and operations
│   ├── handlers/          # Telegram command handlers
│   ├── rutor/             # rutor.info parser
│   ├── tasks/             # Background tasks
│   └── torrent_clients/   # Torrent client implementations
├── alembic/               # Database migrations
├── docker-compose.yml     # Production deployment
└── docs/                  # Documentation
```

### Components

1. **Telegram Bot** - Main user interface
2. **TaskIQ Scheduler** - Periodic task scheduler
3. **TaskIQ Workers** - Background task workers
4. **Database** - PostgreSQL/SQLite for data storage
5. **Redis** - Message broker for TaskIQ (optional)

## Development

### Running Tests

```bash
uv run pytest
```

### Code Quality

```bash
# Linting
uv run ruff check

# Formatting
uv run ruff format

# Type checking
uv run mypy src
```

### Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

## Troubleshooting

### Bot Not Responding

1. Check bot token in configuration
2. Ensure your Telegram ID is in `users_white_list`
3. Check logs: `docker-compose logs bot`

### Download Errors

1. Check torrent client availability
2. Verify connection settings
3. Check torrent client logs

### Access Issues with rutor.info

1. Configure proxy in settings:
   ```toml
   proxy = "socks5://localhost:1080"
   ```
2. Verify proxy server availability

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
