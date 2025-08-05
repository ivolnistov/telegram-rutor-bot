# Torrent Client Configuration

The bot supports two torrent clients: Transmission and qBittorrent.

## Configuration

Set the `torrent_client` option in your `config.toml`:

```toml
# Choose torrent client: transmission or qbittorrent
torrent_client = "transmission"
```

## Transmission Configuration

```toml
transmission_host = "localhost"
transmission_port = 9091
transmission_username = "admin"
transmission_password = "password"
```

## qBittorrent Configuration

```toml
qbittorrent_host = "localhost"
qbittorrent_port = 8080
qbittorrent_username = "admin"
qbittorrent_password = "adminadmin"
```

## Docker Compose

When using Docker Compose, you can set the torrent client via environment variables:

```bash
# Using Transmission
TORRENT_CLIENT=transmission docker-compose up

# Using qBittorrent
TORRENT_CLIENT=qbittorrent \
QBITTORRENT_HOST=qbittorrent \
QBITTORRENT_PORT=8080 \
QBITTORRENT_USERNAME=admin \
QBITTORRENT_PASSWORD=adminadmin \
docker-compose up
```

## Adding Torrent Client Service to Docker Compose

### Transmission Example

```yaml
transmission:
  image: linuxserver/transmission
  environment:
    - PUID=1000
    - PGID=1000
    - TZ=Europe/London
    - USER=admin
    - PASS=password
  volumes:
    - ./transmission/config:/config
    - ./downloads:/downloads
  ports:
    - 9091:9091
    - 51413:51413
    - 51413:51413/udp
```

### qBittorrent Example

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

Both clients support:
- Adding torrents by magnet link
- Listing torrents
- Getting torrent information
- Pausing/resuming torrents
- Removing torrents (with optional file deletion)

## API Implementation

The bot uses a unified interface for both clients:
- Transmission: Uses JSON-RPC API via httpx
- qBittorrent: Uses Web API v2 via httpx

Both implementations are fully async and don't require additional dependencies beyond httpx.
