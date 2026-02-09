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


async def check_matches(session: AsyncSession, new_torrents: list[Torrent]) -> None:
    """
    Check if any of the new torrents match pending watchlist items.
    If match found -> Download and set film to downloaded.
    """
    if not new_torrents:
        return

    # Get all watching films
    # We delay imports to avoid circular deps if necessary,
    # but db imports are generally safe here.

    stmt = select(Film).where(Film.watch_status == 'watching')
    watching_films = (await session.execute(stmt)).scalars().all()

    if not watching_films:
        return

    # Check each film against new torrents
    for film in watching_films:
        # Filter new torrents relevant to this film (by fuzzy name)
        # Optimization: We check "potential matches"
        # Since we rely on passive search, we just checking everything?
        # Ideally we only check torrents that match the film name.

        relevant_torrents = []
        film_query = film.name.lower()
        if film.original_title:
            film_query = film.original_title.lower()

        for t in new_torrents:
            # Fuzzy match title
            score = fuzz.partial_ratio(film_query, t.name.lower())
            if score >= 90:  # High confidence that this torrent is about this film
                relevant_torrents.append(t)

        if not relevant_torrents:
            continue

        best = select_best_torrent(relevant_torrents, film)
        if best:
            log.info('Auto-match found for watchlist item %s: %s', film.name, best.name)

            # Download
            client = get_torrent_client()
            await client.connect()
            try:
                await client.add_torrent(best.magnet)
                film.watch_status = 'downloaded'
                film.notified = False  # To be picked up by digest
                await session.commit()
            except Exception as e:
                log.error('Failed to auto-download watchlist item %s: %s', film.name, e)
            finally:
                await client.disconnect()
