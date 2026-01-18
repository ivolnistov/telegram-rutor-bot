"""Torrent client abstraction layer"""

from .base import TorrentClient, TorrentClientError
from .factory import get_torrent_client
from .qbittorrent import QBittorrentClient

__all__ = [
    'QBittorrentClient',
    'TorrentClient',
    'TorrentClientError',
    'get_torrent_client',
]
