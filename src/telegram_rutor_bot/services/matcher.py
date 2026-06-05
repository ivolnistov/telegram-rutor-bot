import difflib
import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.clients.tmdb import TmdbClient
from telegram_rutor_bot.db.films import get_unlinked_films, update_film_metadata
from telegram_rutor_bot.db.models import Film

log = logging.getLogger(__name__)

# Title-similarity threshold for accepting a TMDB match.
# Below this, treat the result as a false positive even if TMDB returned it.
_SIMILARITY_THRESHOLD = 0.6


def _normalize(s: str | None) -> str:
    """Lowercase and strip non-word characters for fuzzy comparison."""
    if not s:
        return ''
    return re.sub(r'\W+', ' ', s.lower(), flags=re.UNICODE).strip()


def _similar(a: str | None, b: str | None) -> float:
    """Return similarity ratio between two normalised strings (0..1)."""
    na, nb = _normalize(a), _normalize(b)
    if not na or not nb:
        return 0.0
    if na == nb or na in nb or nb in na:
        return 1.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def _result_year(result: dict[str, Any]) -> int | None:
    date = result.get('release_date') or result.get('first_air_date') or ''
    try:
        return int(date[:4]) if date[:4].isdigit() else None
    except (ValueError, TypeError):
        return None


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
                    )
                    matched_count += 1
                    log.info(f"Matched film '{film.name}' to TMDB ID {match['id']}")
            except Exception as e:
                log.error(f'Error matching film {film.id}: {e}')

        return matched_count

    @staticmethod
    def _best_match(results: list[dict[str, Any]], query: str, year: int | None) -> dict[str, Any] | None:
        """Pick the best result, enforcing year match and title similarity.

        TMDB's `year` filter is loose: it can return wrong-year results when no
        exact-year match exists (e.g. searching `Утес` 2026 returns `Рыбка Поньо
        на утёсе` 2008). We re-filter client-side and verify title similarity to
        avoid blindly accepting results[0].
        """
        if not results:
            return None

        # Strict year filter (allow ±1 to accommodate Russian/Western release-date drift).
        if year:
            year_filtered = [r for r in results if (ry := _result_year(r)) and abs(ry - year) <= 1]
        else:
            year_filtered = list(results)

        if not year_filtered:
            return None

        # Score each remaining candidate by max title similarity.
        scored: list[tuple[float, dict[str, Any]]] = []
        for r in year_filtered:
            score = max(
                _similar(query, r.get('title')),
                _similar(query, r.get('original_title')),
                _similar(query, r.get('name')),
                _similar(query, r.get('original_name')),
            )
            scored.append((score, r))

        scored.sort(key=lambda s: s[0], reverse=True)
        best_score, best = scored[0]

        if best_score >= _SIMILARITY_THRESHOLD:
            return best

        # Single year-matched result with weak title similarity is still a likely match
        # (e.g. transliteration differences).
        if len(year_filtered) == 1:
            return year_filtered[0]

        return None

    async def _try_find_tmdb_match(self, film: Film) -> dict[str, Any] | None:
        # Try multiple query variants in priority order.
        queries: list[str] = []
        if film.name:
            queries.append(film.name)
        if film.original_title and film.original_title != film.name:
            queries.append(film.original_title)
        if film.ru_name and film.ru_name not in queries:
            queries.append(film.ru_name)

        # Also try a release-marker-cleaned variant of the primary name.
        if film.name:
            cleaned = re.sub(
                r'(?i)(3d|3д|4k|4к|imax|extended|directors?[\s\.]*cut|unrated|\btheatrical\b)',
                '',
                film.name,
            )
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            if cleaned and cleaned not in queries:
                queries.append(cleaned)

        for query in queries:
            results = await self.tmdb.search_movie(query, year=film.year)
            match = self._best_match(results, query, film.year)
            if match:
                if query != film.name:
                    log.info(f"Matched '{film.name}' via fallback query '{query}' -> tmdb-{match['id']}")
                return match

        log.info(f"No confident TMDB match for '{film.name}' ({film.year})")
        return None
