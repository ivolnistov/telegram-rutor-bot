"""Telegram bot command handlers module"""

from .commons import (
    add_user_cmd,
    help_handler,
    language_handler,
    set_language_callback,
    start,
    unknown,
)
from .search import search_callback_handler, search_delete, search_execute, search_list
from .subscribe import subscribe, subscriptions_list, unsubscribe
from .torrents import (
    callback_query_handler,
    download_torrent,
    torrent_download,
    torrent_downloads,
    torrent_info,
    torrent_list,
    torrent_recommend,
    torrent_search,
)
from .watchlist import watch_command

__all__ = [
    'add_user_cmd',
    'callback_query_handler',
    'download_torrent',
    'help_handler',
    'language_handler',
    'search_callback_handler',
    'search_delete',
    'search_execute',
    'search_list',
    'set_language_callback',
    'start',
    'subscribe',
    'subscriptions_list',
    'torrent_download',
    'torrent_downloads',
    'torrent_info',
    'torrent_list',
    'torrent_recommend',
    'torrent_search',
    'unknown',
    'unsubscribe',
    'watch_command',
]
