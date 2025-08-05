"""Factory for creating torrent client instances"""

from telegram_rutor_bot.config import settings

from .base import TorrentClient
from .qbittorrent import QBittorrentClient
from .transmission import TransmissionClient


def get_torrent_client() -> TorrentClient:
    """Get torrent client instance based on configuration

    Returns:
        TorrentClient instance (Transmission or qBittorrent)
    """
    client_type = str(settings.torrent_client).lower()

    if client_type == 'qbittorrent':
        return QBittorrentClient(
            host=settings.qbittorrent_host,
            port=settings.qbittorrent_port,
            username=settings.qbittorrent_username,
            password=settings.qbittorrent_password,
        )
    if client_type == 'transmission':
        return TransmissionClient(
            host=settings.transmission_host,
            port=settings.transmission_port,
            username=settings.transmission_username,
            password=settings.transmission_password,
        )
    raise ValueError(f'Unknown torrent client: {client_type}')
