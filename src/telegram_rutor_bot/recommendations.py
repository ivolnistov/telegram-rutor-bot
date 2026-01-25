"""Movie recommendation engine based on user history."""

from __future__ import annotations

import logging
from collections import Counter
from typing import TYPE_CHECKING

from sqlalchemy import desc, select

from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db.models import Film, Torrent

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(f'{settings.log_prefix}.recommendations')


async def get_user_preferences(session: AsyncSession) -> dict[str, float]:
    """
    Analyze downloaded films to determine genre preferences.
    Returns a dictionary of {genre: weight} where weight is 0.0-1.0
    """
    # Get all films that have at least one downloaded torrent
    stmt = select(Film.genres).join(Torrent).where(Torrent.downloaded.is_(True)).where(Film.genres.is_not(None))
    result = await session.execute(stmt)
    downloaded_genres_raw = result.scalars().all()

    if not downloaded_genres_raw:
        return {}

    # Flatten genres list (films can have "Action, Sci-Fi")
    all_genres = []
    for g_str in downloaded_genres_raw:
        if g_str:
            genres = [g.strip() for g in g_str.split(',')]
            all_genres.extend(genres)

    if not all_genres:
        return {}

    # Calculate frequency
    counts = Counter(all_genres)
    total = sum(counts.values())

    # Normalize to 0-1
    # Normalize to 0-1
    return {genre: count / total for genre, count in counts.items()}


async def get_recommendations(session: AsyncSession, limit: int = 5) -> list[Film]:
    """
    Get recommended films based on genre preferences.
    Excludes already downloaded films.
    """
    prefs = await get_user_preferences(session)
    if not prefs:
        # If no history, return top rated films
        stmt = select(Film).where(Film.rating.is_not(None)).order_by(desc(Film.rating)).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # Get IDs of downloaded films to exclude
    downloaded_subquery = select(Torrent.film_id).where(Torrent.downloaded.is_(True))

    # Fetch candidates (films with genres and rating, not downloaded)
    # Fetching all potential candidates to score in python is safer for complex scoring
    # but we can filter a bit in SQL
    stmt = (
        select(Film).where(Film.id.not_in(downloaded_subquery)).where(Film.genres.is_not(None))
        # .where(Film.rating.is_not(None)) # Optional: only recommend rated films
    )
    result = await session.execute(stmt)
    candidates = result.scalars().all()

    scored_candidates = []
    for film in candidates:
        score = 0.0

        # Genre score
        if film.genres:
            film_genres = [g.strip() for g in film.genres.split(',')]
            for genre in film_genres:
                score += prefs.get(genre, 0.0)

        # Rating boost (0-1 point)
        # Assuming rating is like "8.5" or "8.5/10"
        try:
            if film.rating:
                rating_val = float(film.rating.split('/')[0])
                score += rating_val / 10.0
        except ValueError, AttributeError:
            pass

        scored_candidates.append((score, film))

    # Sort by score desc
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    return [film for _, film in scored_candidates[:limit]]
