# Single Container Deployment

This guide describes how to run the Telegram Rutor Bot in a single container, suitable for small deployments or personal use.

## Overview

The single-container deployment includes:
- Telegram bot
- TaskIQ scheduler and worker (using in-memory broker)
- SQLite database (file-based)
- All components run in a single process using Python multiprocessing

## Prerequisites

- Docker and Docker Compose installed
- Telegram bot token from [@BotFather](https://t.me/botfather)
- Access to qBittorrent

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/telegram-rutor-bot.git
cd telegram-rutor-bot
```

### 2. Create configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Required
TELEGRAM_TOKEN=your-bot-token-here

# Torrent client (qBittorrent is default)
QBITTORRENT_HOST=localhost
QBITTORRENT_PORT=8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin

# Optional proxy for rutor.info
# PROXY=socks5://localhost:1080
```

### 3. Run with Docker Compose

```bash
docker-compose -f docker-compose.single.yml up -d
```

### 4. Check logs

```bash
docker-compose -f docker-compose.single.yml logs -f
```

## Configuration

### Environment Variables

All settings can be configured via environment variables with the `RUTOR_BOT_` prefix:

| Variable | Description | Default |
|----------|-------------|---------|
| `RUTOR_BOT_TELEGRAM_TOKEN` | Telegram bot token | Required |
| `RUTOR_BOT_QBITTORRENT_HOST` | qBittorrent Web UI host | `localhost` |
| `RUTOR_BOT_QBITTORRENT_PORT` | qBittorrent Web UI port | `8080` |
| `RUTOR_BOT_PROXY` | Proxy URL for accessing rutor.info | None |
| `RUTOR_BOT_LOG_LEVEL` | Log level: DEBUG, INFO, WARNING, ERROR | `INFO` |

### Data Persistence

The bot stores its data in `/app/data` inside the container, which is mounted as a Docker volume:

- `rutor.db` - SQLite database with movies, torrents, and subscriptions
- Cache files for movie information

### Network Modes

#### Host Network (recommended if torrent client is on the same machine)

Uncomment in `docker-compose.single.yml`:

```yaml
network_mode: host
```

#### Bridge Network (default)

The bot runs in an isolated network. Make sure to use proper hostnames:
- Use `host.docker.internal` for the Docker host (macOS/Windows)
- Use actual IP addresses for Linux

## Building Custom Image

To build the single-container image manually:

```bash
docker build -f Dockerfile.single -t telegram-rutor-bot:single .
```

## Running Without Docker

For development or testing, you can run the single-container mode locally:

```bash
./run_single.sh
```

This script will:
1. Create a virtual environment
2. Install dependencies
3. Run database migrations
4. Start all components in a single process

## Monitoring

### Health Check

The container includes a health check that verifies:
- Database file exists
- Application is responsive

Check health status:

```bash
docker inspect telegram-rutor-bot | jq '.[0].State.Health'
```

### Logs

View logs using Docker Compose:

```bash
# View all logs
docker-compose -f docker-compose.single.yml logs

# Follow logs in real-time
docker-compose -f docker-compose.single.yml logs -f

# View last 100 lines
docker-compose -f docker-compose.single.yml logs --tail=100
```

## Backup

To backup your data:

```bash
# Stop the container
docker-compose -f docker-compose.single.yml down

# Backup the volume
docker run --rm \
  -v telegram-rutor-bot_bot-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/bot-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restart the container
docker-compose -f docker-compose.single.yml up -d
```

## Troubleshooting

### Bot doesn't respond to commands

1. Verify the bot token is correct
2. Check logs for errors

### Can't connect to torrent client

1. Verify the torrent client is running and accessible
2. Check firewall rules
3. If using Docker host network, ensure no port conflicts

### Database errors

1. Check if the data volume has proper permissions
2. Remove the volume and let it recreate: `docker volume rm telegram-rutor-bot_bot-data`

## Limitations

The single-container deployment:
- Uses SQLite (not suitable for high load)
- Uses in-memory task broker (tasks don't survive restarts)
- All components run in one process (less fault-tolerant)

For production deployments with high availability requirements, use the [multi-container setup](deployment.md).
