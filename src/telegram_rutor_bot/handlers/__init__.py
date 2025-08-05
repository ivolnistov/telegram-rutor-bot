"""Telegram bot command handlers module"""

from .commons import start, unknown
from .search import search_add, search_delete, search_execute, search_list
from .subscribe import subscribe, subscriptions_list, unsubscribe
from .torrents import (
    download_torrent,
    torrent_download,
    torrent_info,
    torrent_list,
    torrent_search,
)

__all__ = [
    # Torrents
    'download_torrent',
    # Search
    'search_add',
    'search_delete',
    'search_execute',
    'search_list',
    # Commons
    'start',
    # Subscribe
    'subscribe',
    'subscriptions_list',
    'torrent_download',
    'torrent_info',
    'torrent_list',
    'torrent_search',
    'unknown',
    'unsubscribe',
]
