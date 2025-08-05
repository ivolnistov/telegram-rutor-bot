"""Rutor.info torrent parser and downloader module."""

from .parser import (
    download_torrent,
    get_file_link,
    get_torrent_details,
    get_torrent_info,
    parse_rutor,
)

__all__ = [
    'download_torrent',
    'get_file_link',
    'get_torrent_details',
    'get_torrent_info',
    'parse_rutor',
]
