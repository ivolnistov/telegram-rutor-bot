# Configuration Guide

The bot uses a hybrid configuration system:
## Configuration Priority

Configuration values are loaded in the following order (later sources override earlier ones):

1. Default values in code
2. Database settings (from Setup Wizard)
3. `config.toml` file
4. Environment variables
5. `.env` file (when using Docker Compose)

## Web UI Setup (Recommended)

When you first run the bot, access the web interface (default: http://localhost:8080 or http://localhost:8088 in hybrid mode) to complete the **Setup Wizard**.
This will configure:
- Telegram Token
- Torrent Client
- Proxy settings
- User access

## Manual Configuration (Advanced)

Manual configuration via `config.toml` or environment variables is useful for headless deployments or overriding DB values.

## Configuration Options

### Telegram Settings

| Option | Type | Required | Description | Default |
|--------|------|----------|-------------|---------|
| `telegram_token` | string | **Yes** | Bot token (set via Wizard or Env) | - |
| `unauthorized_message` | string | No | Message shown to unauthorized users | "Unauthorized user..." |

### Network Settings (Hybrid)

| Option | Type | Required | Description | Default |
|--------|------|----------|-------------|---------|
| `proxy` | string | No | Proxy URL (set via Wizard or Env) | - |
| `timeout` | integer | No | Request timeout in seconds | 60 |

Example:
```toml
telegram_token = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
proxy = "socks5://localhost:1080"
timeout = 30
```

### Environment Variables

All configuration options can be set via environment variables by prefixing with `RUTOR_BOT_` and using uppercase:

```bash
export RUTOR_BOT_TELEGRAM_TOKEN="your-token"
export RUTOR_BOT_PROXY="socks5://localhost:1080"
export RUTOR_BOT_DATABASE_URL="postgresql://user:pass@host/db"
```

### Minimal Configuration

```toml
telegram_token = "your-bot-token"
```

### Development Configuration

```toml
telegram_token = "your-bot-token"
log_level = "DEBUG"
database_path = "var/dev.db"

# qBittorrent
qbittorrent_host = "localhost"
qbittorrent_port = 8080
```

### Production Configuration

```toml
telegram_token = "your-bot-token"
log_level = "INFO"

# PostgreSQL
database_url = "postgresql://rutor:password@postgres:5432/rutorbot"

# Redis for TaskIQ
redis_url = "redis://redis:6379"

# qBittorrent in Docker
qbittorrent_host = "qbittorrent"
qbittorrent_port = 8080
qbittorrent_username = "admin"
qbittorrent_password = "adminadmin"  # gitleaks:allow

# Proxy for accessing rutor.info
proxy = "socks5://proxy:1080"

# Limit torrent size to 10GB
size_limit = 10737418240
```

### Docker Compose Configuration

When using Docker Compose, create a `.env` file:

```bash
# Telegram
TELEGRAM_TOKEN=your-bot-token

# Torrent Client (qBittorrent)
QBITTORRENT_HOST=qbittorrent
QBITTORRENT_PORT=8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin

# Optional proxy
PROXY=socks5://proxy:1080
```

## Validating Configuration

The bot validates configuration on startup. Common validation errors:

- **Missing telegram_token**: Bot token is required
- **Invalid database_url**: PostgreSQL URL must be in correct format
- **Invalid proxy URL**: Proxy must be a valid URL with scheme

## Security Considerations

1. **Never commit sensitive data**: Keep `config.toml` and `.env` out of version control
2. **Use strong passwords**: For torrent clients and database
3. **Secure proxy**: If using proxy, ensure it's trusted and secure
4. **File permissions**: Restrict access to configuration files:
   ```bash
   chmod 600 config.toml
   chmod 600 .env
   ```
