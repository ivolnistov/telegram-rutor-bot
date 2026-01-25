import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.clients.tmdb import TmdbClient
from telegram_rutor_bot.db.films import get_unlinked_films, update_film_metadata

log = logging.getLogger(__name__)


class TmdbMatcher:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tmdb = TmdbClient()

    async def match_films(self, limit: int = 50) -> int:
        """
        Match unlinked films with TMDB.
        Returns number of matched films.
        """
        films = await get_unlinked_films(self.session, limit=limit)
        matched_count = 0

        for film in films:
            try:
                # Try to search specifically by year first if available
                # Assuming film.year is reliable.
                # If film.name is Russian, search might fail if TMDB expects English or user language?
                # TmdbClient uses 'ru-RU' by default via config, so searching Russian name is fine.

                query = film.name

                # Check if it's likely a show or movie?
                # We don't know, default to movie logic first? Or search multi?
                # Let's try search_multi to be safe, or just search_movie if most are movies.
                # However, many items on rutor are movies.

                # Let's use search_movie first with year match
                results = await self.tmdb.search_movie(query, year=film.year)

                if not results:
                    # Try cleaning name (remove 3D, 4K, etc)

                    # Remove common quality/edition markers (case insensitive)
                    # 3D, 3Д, 4K, 4K (cyrillic K), IMAX, Extended, Director's Cut
                    cleaned = re.sub(
                        r'(?i)(3d|3д|4k|4к|imax|extended|directors?[\s\.]*cut|unrated|\btheatrical\b)', '', query
                    )
                    # Remove excess whitespace
                    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

                    if cleaned and cleaned != query:
                        log.info(f"Retrying match with cleaned name: '{cleaned}' (was '{query}')")
                        results = await self.tmdb.search_movie(cleaned, year=film.year)

                if not results and film.ru_name:
                    results = await self.tmdb.search_movie(film.ru_name, year=film.year)

                match = None
                if results:
                    # Pick the best match.
                    # If searched with year, first result is likely good.
                    match = results[0]

                if match:
                    await update_film_metadata(
                        self.session,
                        film_id=film.id,
                        tmdb_id=match['id'],
                        tmdb_media_type='movie',  # Assuming movie for now based on search_movie
                        # Could also update poster/rating here?
                        # Let's just link id for now.
                    )
                    matched_count += 1
                    log.info(f"Matched film '{film.name}' to TMDB ID {match['id']}")
            except Exception as e:
                log.error(f'Error matching film {film.id}: {e}')

        return matched_count
