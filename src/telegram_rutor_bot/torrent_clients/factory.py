"""Factory for creating torrent client instances"""

from telegram_rutor_bot.config import settings

from .base import TorrentClient
from .qbittorrent import QBittorrentClient


def get_torrent_client() -> TorrentClient:
    """Get torrent client instance based on configuration

    Returns:
        TorrentClient instance (qBittorrent)
    """
    return QBittorrentClient(
        host=settings.qbittorrent_host,
        port=settings.qbittorrent_port,
        username=settings.qbittorrent_username,
        password=settings.qbittorrent_password,
    )
