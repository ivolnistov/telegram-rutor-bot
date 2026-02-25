"""Watchlist Telegram bot command handlers"""

import contextlib
import logging

from sqlalchemy import select
from telegram import Update
from telegram.ext import ContextTypes

from telegram_rutor_bot.db import get_async_session
from telegram_rutor_bot.db.models import Film
from telegram_rutor_bot.tasks.jobs import search_film_on_rutor
from telegram_rutor_bot.utils import security

log = logging.getLogger(__name__)


@security()
async def watch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a film to the watchlist with optional filters"""
    assert update.message is not None
    assert update.effective_chat is not None
    assert update.message.text is not None

    text = update.message.text
    if text == '/watch':
        msg = (
            'Usage: /watch <Movie Name> [voice:<filter>] [min:<GB>] [max:<GB>] [size:<GB>]\n\n'
            'Example: /watch Breaking Bad voice:LostFilm min:5 max:20\n'
            'Example: /watch Interstellar size:15'
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        return

    # Parse arguments
    args_text = text[len('/watch ') :].strip()
    name, params = _parse_watch_args(args_text)

    if not name:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Error: Movie name is required.')
        return

    async with get_async_session() as session:
        # Check if film exists
        stmt = select(Film).where(Film.name == name)  # Exact match for now
        # NOTE: Ideally should use TMDB to normalize name, but for now simple string match
        film = (await session.execute(stmt)).scalars().first()

        if not film:
            film = Film(name=name, year=0, blake='', monitored=True)  # Basic init
            session.add(film)

        # Update watchlist fields
        film.watch_status = 'watching'
        v_filter = params.get('voice')
        if isinstance(v_filter, str):
            film.voiceover_filter = v_filter

        min_size = params.get('min')
        if isinstance(min_size, float):
            film.min_size_gb = min_size

        max_size = params.get('max')
        if isinstance(max_size, float):
            film.max_size_gb = max_size

        target_size = params.get('size')
        if isinstance(target_size, float):
            film.target_size_gb = target_size

        # Reset notified status if re-adding
        film.notified = False

        await session.commit()

        msg = (
            f'✅ <b>Added to Watchlist</b>\n'
            f'🎬 Name: {film.name}\n'
            f'🔈 Voice: {film.voiceover_filter or "Any"}\n'
            f'📏 Min: {film.min_size_gb or "-"} GB\n'
            f'📏 Max: {film.max_size_gb or "-"} GB\n'
            f'🎯 Target: {film.target_size_gb or "-"} GB\n'
        )

        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode='HTML')

        # Trigger immediate search
        # We need to run this in background or await it?
        # Ideally await it to give feedback "Searching now..."?
        # But parsing takes time. Let's just launch it.
        # We don't have search_film_on_rutor logic to check matches yet.
        # We need to update search_film_on_rutor in jobs.py as well to use check_matches!
        # But assuming it does (or I will update it next), we call it.
        await search_film_on_rutor.kiq(film.id, film.name)


def _parse_watch_args(text: str) -> tuple[str, dict[str, str | float]]:
    """Parse watch command arguments"""
    tokens = text.split()
    name_parts = []
    params: dict[str, str | float] = {}

    for token in tokens:
        lower = token.lower()
        if lower.startswith('voice:'):
            params['voice'] = token.split(':', 1)[1]
        elif lower.startswith('min:'):
            with contextlib.suppress(ValueError):
                params['min'] = float(token.split(':', 1)[1])
        elif lower.startswith('max:'):
            with contextlib.suppress(ValueError):
                params['max'] = float(token.split(':', 1)[1])
        elif lower.startswith('size:'):
            with contextlib.suppress(ValueError):
                params['size'] = float(token.split(':', 1)[1])
        else:
            name_parts.append(token)

    return ' '.join(name_parts), params
