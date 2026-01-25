# Deployment Guide

## Overview

The bot supports multiple deployment scenarios:

- **Development**: Local SQLite with in-memory task queue
- **Single Container**: Docker with SQLite and in-memory queue (recommended for personal use)
- **Multi-Container**: Docker Compose with PostgreSQL and Redis (recommended for production)

### Choosing Deployment Mode

**Use Single Container Mode when:**

- Personal or small team use
- Running on a single server or VPS
- Have low traffic (< 100 users)
- Want simple setup without external dependencies
- Don't need high availability

**Use Multi-Container Mode when:**

- Deploying to production with many users
- Need high availability and fault tolerance
- Have many users or searches (> 100)
- Want to scale workers independently
- Need persistent message queue (Redis)
- Require database replication

## Development Deployment

### Prerequisites

- Python 3.13+
- Transmission or qBittorrent installed locally

### Steps

1. Install dependencies:

```bash
uv sync
```

1. Configure `config.toml`:

```toml
telegram_token = "your-token"
qbittorrent_host = "qbittorrent"
database_path = "var/rutor.db"
```

1. Run migrations:

```bash
uv run alembic upgrade head
```

1. Start services:

```bash
# All services in one terminal
./run_single.sh

# Or run individual components (development only)
uv run telegram-rutor-bot bot      # Telegram bot
uv run telegram-rutor-bot scheduler # TaskIQ scheduler
uv run telegram-rutor-bot worker    # TaskIQ worker
```

## Single Container Docker Deployment

Ideal for personal use or small deployments. All components run in a single container.

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Access to torrent client (Transmission or qBittorrent)

### Quick Start

1. Create `.env`:

```bash
# Required
TELEGRAM_TOKEN=your-bot-token
USERS_WHITE_LIST=123456789,987654321

# Torrent client
TORRENT_CLIENT=qbittorrent
QBITTORRENT_HOST=host.docker.internal  # For macOS/Windows
# QBITTORRENT_HOST=172.17.0.1  # For Linux (Docker bridge IP)
QBITTORRENT_PORT=8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin

# Optional
# PROXY=socks5://localhost:1080
```

1. Deploy:

```bash
docker-compose -f docker-compose.single.yml up -d
```

1. Check logs:

```bash
docker-compose -f docker-compose.single.yml logs -f
```

### Architecture

- **Database**: SQLite (file-based, in Docker volume)
- **Task Queue**: In-memory (using Python multiprocessing)
- **Process Management**: All components in single Python process
- **Data Persistence**: Docker volume for database and cache

See [Single Container Guide](single-container.md) for detailed configuration and troubleshooting.

## Environment Variables

All configuration can be overridden with environment variables using the `RUTOR_BOT_` prefix:

- `RUTOR_BOT_TELEGRAM_TOKEN` - Telegram bot token
- `RUTOR_BOT_USERS_WHITE_LIST` - Comma-separated list of authorized user IDs
- `RUTOR_BOT_DATABASE_URL` - PostgreSQL connection string (multi-container mode)
- `RUTOR_BOT_REDIS_URL` - Redis connection string (multi-container mode)
- `RUTOR_BOT_TRANSMISSION_HOST` - Transmission RPC host
- `RUTOR_BOT_TRANSMISSION_PORT` - Transmission RPC port
- `RUTOR_BOT_TRANSMISSION_USERNAME` - Transmission username
- `RUTOR_BOT_TRANSMISSION_PASSWORD` - Transmission password
- `RUTOR_BOT_PROXY` - Proxy URL (e.g., socks5://host:port)
- `RUTOR_BOT_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## Production Deployment

Full-featured deployment with high availability.

### Architecture

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Bot       │     │  Scheduler  │     │  Workers    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                    │
       └───────────────────┴────────────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
         ┌──────┴──────┐      ┌──────┴──────┐
         │  PostgreSQL │      │    Redis    │
         └─────────────┘      └─────────────┘
```

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Domain/VPS for hosting

### Configuration

1. Create production `.env`:

```bash
# Telegram
TELEGRAM_TOKEN=your-production-token
USERS_WHITE_LIST=123456789,987654321

# Torrent Client
TORRENT_CLIENT=transmission
TRANSMISSION_HOST=transmission
TRANSMISSION_PORT=9091
TRANSMISSION_USERNAME=admin
TRANSMISSION_PASSWORD=secure_password

# Optional
PROXY=socks5://proxy:1080
```

1. Create `docker-compose.override.yml` for customization:

```yaml
version: '3.8'

services:
  transmission:
    image: linuxserver/transmission
    environment:
      - PUID=1000
      - PGID=1000
      - USER=admin
      - PASS=${TRANSMISSION_PASSWORD}
    volumes:
      - ./transmission:/config
      - ./downloads:/downloads
    ports:
      - "9091:9091"
      - "51413:51413"
      - "51413:51413/udp"
```

1. Deploy:

```bash
docker-compose up -d
```

### Scaling Workers

To handle more load, scale workers:

```bash
docker-compose up -d --scale worker=3
```

## Cloud Platform Deployment

### DigitalOcean

1. Create a Droplet (2GB RAM minimum)
2. Install Docker:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

1. Clone repository and configure
2. Run Docker Compose

### AWS EC2

1. Launch EC2 instance (t3.small or larger)
2. Security group rules:
   - SSH (22)
   - HTTP/HTTPS (80/443) if using web UI
   - Torrent ports if needed

3. Install Docker and deploy

### Kubernetes

See `k8s/` directory for Kubernetes manifests (if available).

## SSL/TLS Configuration

For secure torrent client access:

### Using Traefik

Add to `docker-compose.override.yml`:

```yaml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=your-email@example.com"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - "./letsencrypt:/letsencrypt"
      - "/var/run/docker.sock:/var/run/docker.sock:ro"

  transmission:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.transmission.rule=Host(`transmission.yourdomain.com`)"
      - "traefik.http.routers.transmission.entrypoints=websecure"
      - "traefik.http.routers.transmission.tls.certresolver=myresolver"
```

## Monitoring

### Health Checks

Docker Compose includes health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Logging

View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f bot

# Last 100 lines
docker-compose logs --tail=100 bot
```

### Metrics

For production monitoring, add Prometheus exporter:

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
```

## Backup and Recovery

### Database Backup

#### PostgreSQL

```bash
# Backup
docker-compose exec postgres pg_dump -U rutor rutorbot > backup.sql

# Restore
docker-compose exec -T postgres psql -U rutor rutorbot < backup.sql
```

#### SQLite

```bash
# Backup
cp var/rutor.db var/rutor.db.backup

# Restore
cp var/rutor.db.backup var/rutor.db
```

### Full Backup

```bash
# Stop services
docker-compose down

# Backup volumes
tar -czf backup.tar.gz var/ postgres_data/ redis_data/

# Start services
docker-compose up -d
```

## Updates

### Zero-Downtime Update

1. Pull latest changes:

```bash
git pull
docker-compose build
```

1. Update services one by one:

```bash
# Update workers first
docker-compose up -d worker

# Update scheduler
docker-compose up -d scheduler

# Update bot last
docker-compose up -d bot
```

### Database Migrations

Always run migrations before updating:

```bash
docker-compose run --rm migrations
```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Single host: Check if `var/` directory exists and is writable
   - Multi-container: Ensure PostgreSQL is healthy before starting other services

2. **TaskIQ broker errors**
   - Single host: No action needed, uses in-memory broker
   - Multi-container: Check Redis is running and accessible

3. **Telegram API errors**
   - Verify bot token is correct
   - Check network connectivity and proxy settings

4. **Transmission connection errors**
   - Ensure Transmission RPC is enabled
   - Verify host, port, username, and password

### Container Won't Start

```bash
# Check logs
docker-compose logs bot

# Check configuration
docker-compose config

# Validate compose file
docker-compose config --quiet
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
docker-compose exec postgres psql -U rutor -d rutorbot -c "SELECT 1"

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Limit memory in docker-compose.yml
services:
  worker:
    mem_limit: 512m
    mem_reservation: 256m
```

## Security Hardening

### 1. Use Secrets

```yaml
secrets:
  telegram_token:
    file: ./secrets/telegram_token.txt

services:
  bot:
    secrets:
      - telegram_token
    environment:
      - RUTOR_BOT_TELEGRAM_TOKEN_FILE=/run/secrets/telegram_token
```

### 2. Network Isolation

```yaml
networks:
  frontend:
  backend:

services:
  bot:
    networks:
      - frontend
      - backend
  postgres:
    networks:
      - backend
```

### 3. Read-Only Filesystem

```yaml
services:
  bot:
    read_only: true
    tmpfs:
      - /tmp
    volumes:
      - ./var:/app/var:rw
```

### 4. Non-Root User

Already implemented in Dockerfile:

```dockerfile
USER appuser
```
