# Installation Guide

## Requirements

- Python 3.13+
- Docker and Docker Compose (for container deployment)
- PostgreSQL 14+ (for production) or SQLite (for development)
- Redis (for distributed task processing)
- Transmission or qBittorrent

## Development Installation

### 1. Install uv

uv is a modern Python package manager:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/telegram-rutor-bot.git
cd telegram-rutor-bot
```

### 3. Install Dependencies

```bash
# Create virtual environment and install dependencies
uv sync

# Activate virtual environment (optional)
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

### 4. Configure Settings

```bash
cp config.toml.example config.toml
```

Edit `config.toml`:

```toml
# Required settings
telegram_token = "YOUR-BOT-TOKEN"
users_white_list = [123456789]  # Your Telegram ID

# Torrent client
torrent_client = "transmission"  # or "qbittorrent"
transmission_host = "localhost"
transmission_port = 9091
transmission_username = "admin"
transmission_password = "password"

# Database (for development)
database_path = "var/rutor.db"
```

### 5. Create Telegram Bot

1. Open [@BotFather](https://t.me/botfather) in Telegram
2. Send `/newbot`
3. Choose name and username for your bot
4. Copy the token and paste in `config.toml`

### 6. Get Your Telegram ID

1. Open [@userinfobot](https://t.me/userinfobot) in Telegram
2. Send any message
3. Copy your ID and add to `users_white_list`

### 7. Initialize Database

```bash
# Apply migrations
uv run alembic upgrade head
```

### 8. Run the Bot

```bash
# Run all components
./run_local.sh all

# Or run components separately
uv run python -m telegram_rutor_bot bot       # Telegram bot
uv run python -m telegram_rutor_bot scheduler # Scheduler
uv run python -m telegram_rutor_bot worker    # Worker
```

## Docker Installation

### 1. Prerequisites

Ensure you have:
- Docker 20.10+
- Docker Compose 2.0+

### 2. Configuration

Create `.env` file for Docker Compose:

```bash
# Telegram
TELEGRAM_TOKEN=your-bot-token
USERS_WHITE_LIST=123456789,987654321

# Torrent client
TORRENT_CLIENT=transmission
TRANSMISSION_HOST=transmission
TRANSMISSION_PORT=9091
TRANSMISSION_USERNAME=admin
TRANSMISSION_PASSWORD=password

# Proxy (optional)
# PROXY=socks5://proxy:1080
```

### 3. Launch

```bash
# Production mode (PostgreSQL + Redis)
docker-compose up -d

# Simplified mode (SQLite + InMemory)
docker-compose -f docker-compose.single.yml up -d
```

### 4. Verify Installation

```bash
# View logs
docker-compose logs -f bot

# Service status
docker-compose ps

# Stop services
docker-compose down
```

## Torrent Client Installation

### Transmission

#### Local Installation

```bash
# Ubuntu/Debian
sudo apt-get install transmission-daemon

# macOS
brew install transmission

# Configure RPC
transmission-daemon --auth --username admin --password password
```

#### Docker

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

### qBittorrent

#### Local Installation

```bash
# Ubuntu/Debian
sudo apt-get install qbittorrent-nox

# Run
qbittorrent-nox --webui-port=8080
```

#### Docker

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

## Proxy Installation (Optional)

If rutor.info is blocked in your region:

### SOCKS5 Proxy via SSH

```bash
# Create SSH tunnel
ssh -D 1080 -N user@your-vps-server
```

### Shadowsocks

```bash
# Install
pip install shadowsocks

# Run client
sslocal -c shadowsocks.json
```

Configure in `config.toml`:

```toml
proxy = "socks5://localhost:1080"
```

## Verification

1. Check bot availability:
   - Open your bot in Telegram
   - Send `/start`
   - Bot should respond

2. Test search:
   - Send `/search movie_name`
   - Should see torrent list

3. Test download:
   - Click `/dl_ID` to download
   - Check torrent client

## Troubleshooting

### ImportError on startup

```bash
# Reinstall dependencies
uv sync --reinstall
```

### Database connection error

```bash
# Check database path
mkdir -p var
touch var/rutor.db

# Reinitialize migrations
uv run alembic upgrade head
```

### Bot not responding

1. Check token in configuration
2. Ensure your ID is in `users_white_list`
3. Check internet connection

### Torrent client connection error

1. Check client is running
2. Verify connection settings
3. Ensure RPC/Web UI is enabled
