# Configuration Guide

The bot can be configured using a TOML file or environment variables.

## Configuration File

The default configuration file is `config.toml` in the project root. You can start with the provided example:

```bash
cp config.toml.example config.toml
```

## Configuration Options

### Telegram Settings

| Option | Type | Required | Description | Default |
|--------|------|----------|-------------|---------|
| `telegram_token` | string | Yes | Bot token from @BotFather | - |
| `users_white_list` | array | Yes | List of authorized Telegram user IDs | [] |
| `unauthorized_message` | string | No | Message shown to unauthorized users | "Unauthorized user, please contact my master" |

Example:
```toml
telegram_token = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
users_white_list = [123456789, 987654321]
unauthorized_message = "Access denied. Contact admin."
```

### Torrent Client Settings

| Option | Type | Required | Description | Default |
|--------|------|----------|-------------|---------|
| `torrent_client` | string | No | Client type: "transmission" or "qbittorrent" | "transmission" |

#### Transmission Settings

| Option | Type | Required | Description | Default |
|--------|------|----------|-------------|---------|
| `transmission_host` | string | No | Transmission RPC host | "localhost" |
| `transmission_port` | integer | No | Transmission RPC port | 9091 |
| `transmission_username` | string | No | RPC username | "" |
| `transmission_password` | string | No | RPC password | "" |

#### qBittorrent Settings

| Option | Type | Required | Description | Default |
|--------|------|----------|-------------|---------|
| `qbittorrent_host` | string | No | qBittorrent Web UI host | "localhost" |
| `qbittorrent_port` | integer | No | qBittorrent Web UI port | 8080 |
| `qbittorrent_username` | string | No | Web UI username | "admin" |
| `qbittorrent_password` | string | No | Web UI password | "adminadmin" |

Example:
```toml
torrent_client = "qbittorrent"
qbittorrent_host = "192.168.1.100"
qbittorrent_port = 8080
qbittorrent_username = "admin"
qbittorrent_password = "secure_password"
```

### Database Settings

| Option | Type | Required | Description | Default |
|--------|------|----------|-------------|---------|
| `database_path` | string | No | SQLite database file path | "var/rutor.db" |
| `database_url` | string | No | PostgreSQL connection URL | - |

Example:
```toml
# For development (SQLite)
database_path = "var/rutor.db"

# For production (PostgreSQL)
database_url = "postgresql://user:password@localhost:5432/rutorbot"
```

### Network Settings

| Option | Type | Required | Description | Default |
|--------|------|----------|-------------|---------|
| `proxy` | string | No | Proxy URL for accessing rutor.info | - |
| `timeout` | integer | No | Request timeout in seconds | 60 |

Example:
```toml
proxy = "socks5://localhost:1080"
timeout = 30
```

### Parser Settings

| Option | Type | Required | Description | Default |
|--------|------|----------|-------------|---------|
| `size_limit` | integer | No | Maximum torrent size in bytes (0 = unlimited) | 0 |

Example:
```toml
size_limit = 5368709120  # 5 GB
```

### Logging Settings

| Option | Type | Required | Description | Default |
|--------|------|----------|-------------|---------|
| `log_prefix` | string | No | Prefix for logger names | "rutorbot" |
| `log_level` | string/int | No | Logging level | "INFO" |

Valid log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Example:
```toml
log_prefix = "mybot"
log_level = "DEBUG"
```

### TaskIQ Settings

| Option | Type | Required | Description | Default |
|--------|------|----------|-------------|---------|
| `redis_url` | string | No | Redis URL for TaskIQ broker | - |

Example:
```toml
redis_url = "redis://localhost:6379/0"
```

## Environment Variables

All configuration options can be set via environment variables by prefixing with `RUTOR_BOT_` and using uppercase:

```bash
export RUTOR_BOT_TELEGRAM_TOKEN="your-token"
export RUTOR_BOT_USERS_WHITE_LIST="[123456789, 987654321]"
export RUTOR_BOT_PROXY="socks5://localhost:1080"
export RUTOR_BOT_DATABASE_URL="postgresql://user:pass@host/db"
```

Environment variables take precedence over config file values.

## Configuration Examples

### Minimal Configuration

```toml
telegram_token = "your-bot-token"
users_white_list = [123456789]
```

### Development Configuration

```toml
telegram_token = "your-bot-token"
users_white_list = [123456789]
log_level = "DEBUG"
database_path = "var/dev.db"

# Local Transmission
transmission_host = "localhost"
transmission_port = 9091
```

### Production Configuration

```toml
telegram_token = "your-bot-token"
users_white_list = [123456789, 987654321]
log_level = "INFO"

# PostgreSQL
database_url = "postgresql://rutor:password@postgres:5432/rutorbot"

# Redis for TaskIQ
redis_url = "redis://redis:6379"

# Transmission in Docker
torrent_client = "transmission"
transmission_host = "transmission"
transmission_port = 9091
transmission_username = "admin"
transmission_password = "secure_password"

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
USERS_WHITE_LIST=123456789,987654321

# Torrent Client
TORRENT_CLIENT=qbittorrent
QBITTORRENT_HOST=qbittorrent
QBITTORRENT_PORT=8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin

# Optional proxy
PROXY=socks5://proxy:1080
```

## Configuration Priority

Configuration values are loaded in the following order (later sources override earlier ones):

1. Default values in code
2. `config.toml` file
3. Environment variables
4. `.env` file (when using Docker Compose)

## Validating Configuration

The bot validates configuration on startup. Common validation errors:

- **Missing telegram_token**: Bot token is required
- **Empty users_white_list**: At least one authorized user ID is required
- **Invalid database_url**: PostgreSQL URL must be in correct format
- **Invalid proxy URL**: Proxy must be a valid URL with scheme

## Security Considerations

1. **Never commit sensitive data**: Keep `config.toml` and `.env` out of version control
2. **Use strong passwords**: For torrent clients and database
3. **Restrict user access**: Only add trusted Telegram IDs to whitelist
4. **Secure proxy**: If using proxy, ensure it's trusted and secure
5. **File permissions**: Restrict access to configuration files:
   ```bash
   chmod 600 config.toml
   chmod 600 .env
   ```
