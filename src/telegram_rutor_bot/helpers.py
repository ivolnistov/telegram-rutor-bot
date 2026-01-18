"""Helper functions for the bot"""

import html
import logging
import re
from collections.abc import Iterable
from hashlib import blake2s
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram_rutor_bot.db import get_async_session, get_torrents_by_film, update_film_metadata
from telegram_rutor_bot.rutor import get_torrent_info
from telegram_rutor_bot.schemas import Notification

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

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


def _format_torrents_buttons(
    torrents: list[Any], film: Film, metadata: dict[str, Any] | None = None
) -> InlineKeyboardMarkup:
    """Format list of torrents as inline buttons"""
    buttons = []

    for t in torrents:
        clean_name = _clean_torrent_name(t.name, film.name, film.year)
        # Truncate clean_name if too long for button
        if len(clean_name) > 30:
            clean_name = clean_name[:27] + '...'

        size = humanize_bytes(t.size)
        # Text: "↓ 1080p (10.5 GB)"
        text = f'⬇️ {clean_name} ({size})'

        row = [InlineKeyboardButton(text, callback_data=f'dl_{t.id}')]

        # Add Rutor button
        rutor_url = urljoin('http://rutor.info', t.link)
        row.append(InlineKeyboardButton('🔗', url=rutor_url))

        buttons.append(row)

    # Add IMDB/KP buttons if metadata exists
    if metadata:
        info_row = []
        if metadata.get('imdb_url'):
            info_row.append(InlineKeyboardButton('⭐ IMDB', url=metadata['imdb_url']))
        if metadata.get('kp_url'):
            info_row.append(InlineKeyboardButton('🎬 KP', url=metadata['kp_url']))

        if info_row:
            buttons.append(info_row)

    return InlineKeyboardMarkup(buttons)


async def _format_film_with_details(session: AsyncSession, film: Film, torrents: list[Any]) -> Notification:
    """Format film with detailed info from first torrent returning structured data"""
    first_torrent = torrents[0]

    try:
        film_info, poster, _, poster_url, metadata = await get_torrent_info(first_torrent.link)

        # Update film poster if available and missing
        if poster_url and not film.poster:
            await update_film_metadata(session, film.id, poster=poster_url)

        # Extract movie info lines
        movie_info_lines = _extract_movie_info_lines(film_info)

        # Build caption
        # Title in bold (HTML)
        safe_name = html.escape(film.name)
        caption_lines = [f'🎬 <b>{safe_name}</b> ({film.year})']

        # We should also escape movie_info_lines just in case they contain < or >
        safe_info_lines = [html.escape(line) for line in movie_info_lines]
        caption_lines.extend(safe_info_lines)

        caption = '\n'.join(caption_lines)

        # Truncate caption if too long (Telegram limit 1024)
        if len(caption) > 1000:
            caption = caption[:997] + '...'

        markup = _format_torrents_buttons(torrents, film, metadata)

        return {
            'type': 'photo' if (poster or poster_url) else 'text',
            'media': poster or poster_url,
            'caption': caption,
            'reply_markup': markup,
        }

    except (OSError, ValueError) as e:
        log.debug('Failed to get torrent info: %s', e)
        return _format_film_simple(film, torrents)


def _format_film_simple(film: Film, torrents: list[Any]) -> Notification:
    """Simple film format without detailed info"""
    safe_name = html.escape(film.name)
    text = f'🎬 <b>{safe_name}</b> ({film.year})'
    markup = _format_torrents_buttons(torrents, film)
    return {
        'type': 'text',
        'media': None,
        'caption': text,
        'reply_markup': markup,
    }


async def format_films(films: Iterable[Film]) -> list[Notification]:
    """Format films for telegram messages, returns list of notification objects"""
    notifications: list[Notification] = []

    async with get_async_session() as session:
        for film in films:
            torrents = await get_torrents_by_film(session, film.id)
            if not torrents:
                continue

            # Format film with details or simple format
            notification = await _format_film_with_details(session, film, torrents)
            notifications.append(notification)

    return notifications
