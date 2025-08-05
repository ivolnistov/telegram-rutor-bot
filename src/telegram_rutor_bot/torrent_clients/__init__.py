"""Torrent client abstraction layer"""

from .base import TorrentClient, TorrentClientError
from .factory import get_torrent_client
from .qbittorrent import QBittorrentClient
from .transmission import TransmissionClient

__all__ = [
    'QBittorrentClient',
    'TorrentClient',
    'TorrentClientError',
    'TransmissionClient',
    'get_torrent_client',
]
