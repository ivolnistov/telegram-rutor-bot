"""Helper functions for the bot"""

import logging
import re
from collections.abc import Iterable
from hashlib import blake2s
from typing import TYPE_CHECKING

from telegram_rutor_bot.db import get_async_session, get_torrents_by_film
from telegram_rutor_bot.rutor import get_torrent_info

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from telegram_rutor_bot.db.models import Film


def gen_hash(text: str, prefix: str | None = None) -> str:
    """Generate a blake2s hash from text with optional prefix"""
    return (prefix or '') + blake2s(text.encode()).hexdigest()


def humanize_bytes(num: float, suffix: str = 'B') -> str:
    """Convert bytes to human readable format"""
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1000.0:
            return f'{num:3.1f} {unit}{suffix}'
        num /= 1000.0
    return f'{num:.1f} Y{suffix}'


def _extract_movie_info_lines(film_info: str) -> list[str]:
    """Extract movie info lines before technical details section"""
    info_lines = film_info.split('\n')
    movie_info_lines = []

    for line in info_lines:
        if '📀 Технические детали:' in line:
            break
        if line.strip():
            movie_info_lines.append(line)

    return movie_info_lines


def _clean_torrent_name(torrent_name: str, film_name: str, film_year: int) -> str:
    """Clean torrent name by removing film name and year"""
    # Remove film name and year in various formats
    clean_name = re.sub(rf'^.*\s\({film_year}\)\s', '', torrent_name)
    clean_name = re.sub(rf'^{re.escape(film_name)}\s*\({film_year}\)\s*', '', clean_name)
    return re.sub(rf'^{re.escape(film_name)}\s+{film_year}\s+', '', clean_name)


def _split_long_message(message: str, max_length: int = 4096) -> list[str]:
    """Split long message into smaller parts"""
    if len(message) <= max_length:
        return [message.strip()]

    messages = []
    parts = message.split('\n')
    current_msg = ''

    for part in parts:
        if len(current_msg) + len(part) + 1 > max_length:
            messages.append(current_msg.strip())
            current_msg = part + '\n'
        else:
            current_msg += part + '\n'

    if current_msg.strip():
        messages.append(current_msg.strip())

    return messages


def _format_torrents_list(torrents: list, film: 'Film') -> str:
    """Format list of torrents as options"""
    lines = []
    for t in torrents:
        clean_name = _clean_torrent_name(t.name, film.name, film.year)
        lines.append(f'   /dl_{t.id} • {clean_name} • {humanize_bytes(t.size)}')
    return '\n'.join(lines)


async def _format_film_with_details(film: 'Film', torrents: list) -> tuple[list[str], bytes | None]:
    """Format film with detailed info from first torrent"""
    first_torrent = torrents[0]

    try:
        film_info, poster, _ = await get_torrent_info(first_torrent.link, f'/dl_{first_torrent.id}')

        # Extract movie info lines
        movie_info_lines = _extract_movie_info_lines(film_info)

        # Build message
        message = '\n'.join(movie_info_lines)
        message += '\n\n📀 Available options:\n'
        message += _format_torrents_list(torrents, film)

        # Split if needed
        messages = _split_long_message(message)

        return messages, poster

    except (OSError, ValueError) as e:
        # Fallback to simple format on error
        log.debug('Failed to get torrent info: %s', e)
        return _format_film_simple(film, torrents), None


def _format_film_simple(film: 'Film', torrents: list) -> list[str]:
    """Simple film format without detailed info"""
    text = f'🎬 {film.name} ({film.year})\n\n📀 Available options:\n'
    text += _format_torrents_list(torrents, film)
    return [text.strip()]


async def format_films(films: Iterable['Film']) -> tuple[list[str], list[tuple[bytes, str]]]:
    """Format films for telegram messages, returns messages and posters"""
    messages = []
    posters = []  # List of (poster_bytes, caption) tuples

    async with get_async_session() as session:
        for film in films:
            torrents = await get_torrents_by_film(session, film.id)
            if not torrents:
                continue

            # Format film with details or simple format
            film_messages, poster = await _format_film_with_details(film, torrents)
            messages.extend(film_messages)

            # Add poster if available
            if poster:
                caption = f'🎬 {film.name} ({film.year})'
                posters.append((poster, caption))

    if not messages:
        messages = ['Torrents list is empty']
    return messages, posters
