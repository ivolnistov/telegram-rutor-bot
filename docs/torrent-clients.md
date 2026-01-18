# Torrent Client Configuration

The bot exclusively supports **qBittorrent** (version 4.1+ is recommended).

## Configuration

qBittorrent settings are defined in `config.toml` or via environment variables.

### qBittorrent Settings

```toml
qbittorrent_host = "localhost"
qbittorrent_port = 8080
qbittorrent_username = "admin"
qbittorrent_password = "adminadmin"
```

## Docker Compose

When using Docker Compose, you can set the torrent client via environment variables:

```bash
QBITTORRENT_HOST=qbittorrent \
QBITTORRENT_PORT=8080 \
QBITTORRENT_USERNAME=admin \
QBITTORRENT_PASSWORD=adminadmin \
docker-compose up
```

## Service Example (Docker Compose)

### qBittorrent

```yaml
qbittorrent:
  image: linuxserver/qbittorrent
  environment:
    - PUID=1000
    - PGID=1000
    - TZ=Europe/London
    - WEBUI_PORT=8080
  volumes:
    - ./qbittorrent/config:/config
    - ./downloads:/downloads
  ports:
    - 8080:8080
    - 6881:6881
    - 6881:6881/udp
```

## Features Supported

- Adding torrents by magnet link
- Listing torrents
- Getting torrent information
- Pausing/resuming torrents
- Removing torrents (with optional file deletion)
- **Managing Seeding Limits**: The bot can directly configure global seeding limits (Ratio, Time, Inactive Time) in qBittorrent.

## API Implementation

The bot uses the qBittorrent Web API v2 via `httpx`. It is fully async and requires no additional dependencies.
