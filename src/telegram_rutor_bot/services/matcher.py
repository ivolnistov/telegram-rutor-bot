import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.clients.tmdb import TmdbClient
from telegram_rutor_bot.db.films import get_unlinked_films, update_film_metadata
from telegram_rutor_bot.db.models import Film

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
                match = await self._try_find_tmdb_match(film)

                if match:
                    await update_film_metadata(
                        self.session,
                        film_id=film.id,
                        tmdb_id=match['id'],
                        tmdb_media_type='movie',
                        poster=match.get('poster_path'),
                        rating=float(match['vote_average']) if match.get('vote_average') is not None else None,
                        # Store genres if available? Need to map IDs to names or store JSON?
                        # Film model has genres string. Match has genre_ids.
                        # For now, let's at least get poster and rating.
                    )
                    matched_count += 1
                    log.info(f"Matched film '{film.name}' to TMDB ID {match['id']}")
            except Exception as e:
                log.error(f'Error matching film {film.id}: {e}')

        return matched_count

    async def _try_find_tmdb_match(self, film: Film) -> dict[str, Any] | None:
        query = film.name
        results = await self.tmdb.search_movie(query, year=film.year)

        if not results:
            cleaned = re.sub(r'(?i)(3d|3д|4k|4к|imax|extended|directors?[\s\.]*cut|unrated|\btheatrical\b)', '', query)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()

            if cleaned and cleaned != query:
                log.info(f"Retrying match with cleaned name: '{cleaned}' (was '{query}')")
                results = await self.tmdb.search_movie(cleaned, year=film.year)

        if not results and film.ru_name:
            results = await self.tmdb.search_movie(film.ru_name, year=film.year)

        if results:
            return results[0]
        return None
