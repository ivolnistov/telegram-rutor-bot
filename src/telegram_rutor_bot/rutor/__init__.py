"""Rutor.info torrent parser and downloader module."""

from .parser import (
    add_torrent_from_page_url,
    download_torrent,
    get_file_link,
    get_torrent_details,
    get_torrent_info,
    parse_rutor,
)

__all__ = [
    'add_torrent_from_page_url',
    'download_torrent',
    'get_file_link',
    'get_torrent_details',
    'get_torrent_info',
    'parse_rutor',
]
