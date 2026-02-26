"""Service for Watchlist logic: Torrent selection and filtering"""

import logging

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.db.models import Film, Torrent
from telegram_rutor_bot.torrent_clients import get_torrent_client

log = logging.getLogger(__name__)


def select_best_torrent(
    torrents: list[Torrent],
    film: Film,
) -> Torrent | None:
    """
    Select the best torrent based on Watchlist preferences.
    """
    if not torrents:
        return None

    candidates = torrents[:]

    # 1. Filter by Size (Hard Constraints)
    if film.max_size_gb:
        max_bytes = film.max_size_gb * 1024 * 1024 * 1024
        candidates = [t for t in candidates if t.size <= max_bytes]

    if film.min_size_gb:
        min_bytes = film.min_size_gb * 1024 * 1024 * 1024
        candidates = [t for t in candidates if t.size >= min_bytes]

    if not candidates:
        log.info('No torrents match size constraints for film %s', film.name)
        return None

    # 2. Filter by Voiceover (Fuzzy Search)
    if film.voiceover_filter:
        voiceover_candidates = []
        target_voice = film.voiceover_filter.lower()

        for t in candidates:
            # Check name for voiceover
            # Partial ratio is good for finding "LostFilm" inside "Breaking Bad (LostFilm)"
            score = fuzz.partial_ratio(target_voice, t.name.lower())
            if score >= 80:  # Threshold
                voiceover_candidates.append((t, score))

        if voiceover_candidates:
            # Sort by score descending
            voiceover_candidates.sort(key=lambda x: x[1], reverse=True)
            # Keep only the best matches (e.g. top 50% or just use the filtered list)
            # Actually, let's just stick with these candidates.
            candidates = [x[0] for x in voiceover_candidates]
        else:
            log.info('No torrents match voiceover "%s" for film %s', film.voiceover_filter, film.name)
            return None

    # 3. Selection (Size Priority)
    # If target_size_gb is set -> find closest
    # Else -> find minimal

    if film.target_size_gb:
        target_bytes = film.target_size_gb * 1024 * 1024 * 1024
        # Sort by absolute difference
        candidates.sort(key=lambda t: abs(t.size - target_bytes))
    else:
        # Default: Minimal size (as requested by user "4GB vs 20GB -> 4GB")
        candidates.sort(key=lambda t: t.size)

    return candidates[0]


def _find_relevant_torrents(film: Film, torrents: list[Torrent]) -> list[Torrent]:
    """Filter torrents relevant to this film using fuzzy matching"""
    relevant_torrents = []
    film_query = (film.original_title or film.name).lower()

    for t in torrents:
        score = fuzz.partial_ratio(film_query, t.name.lower())
        if score >= 90:  # High confidence
            relevant_torrents.append(t)
    return relevant_torrents


async def _download_best_torrent_for_film(session: AsyncSession, film: Film, torrents: list[Torrent]) -> None:
    """Find and download the best torrent for a given film"""
    relevant_torrents = _find_relevant_torrents(film, torrents)
    if not relevant_torrents:
        return

    best = select_best_torrent(relevant_torrents, film)
    if not best:
        return

    log.info('Auto-match found for watchlist item %s: %s', film.name, best.name)
    client = get_torrent_client()
    await client.connect()
    try:
        tags = f'tmdb:{film.tmdb_id}' if film.tmdb_id else None
        await client.add_torrent(best.magnet, tags=tags)
        film.watch_status = 'downloaded'
        film.notified = False  # To be picked up by digest
        await session.commit()
    except Exception as e:
        log.error('Failed to auto-download watchlist item %s: %s', film.name, e)
    finally:
        await client.disconnect()


async def check_matches(session: AsyncSession, new_torrents: list[Torrent]) -> None:
    """Check if any of the new torrents match pending watchlist items."""
    if not new_torrents:
        return

    stmt = select(Film).where(Film.watch_status == 'watching')
    watching_films = (await session.execute(stmt)).scalars().all()

    for film in watching_films:
        await _download_best_torrent_for_film(session, film, new_torrents)
