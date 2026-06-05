"""Episode notification tracking for series searches."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from .models import NotifiedEpisode


async def get_notified_episodes(session: AsyncSession, search_id: int, film_id: int) -> set[tuple[int, int | None]]:
    """Return set of (season, episode) already notified for this search+film."""
    result = await session.execute(
        select(NotifiedEpisode.season, NotifiedEpisode.episode).where(
            NotifiedEpisode.search_id == search_id,
            NotifiedEpisode.film_id == film_id,
        )
    )
    return {(row.season, row.episode) for row in result.all()}


async def mark_episodes_notified(
    session: AsyncSession,
    search_id: int,
    film_id: int,
    episodes: list[tuple[int, int | None]],
) -> None:
    """Record that these (season, episode) pairs have been notified."""
    if not episodes:
        return

    values = [{'search_id': search_id, 'film_id': film_id, 'season': s, 'episode': e} for s, e in episodes]

    stmt = pg_insert(NotifiedEpisode).values(values).on_conflict_do_nothing(constraint='uq_notified_episode')
    await session.execute(stmt)
    await session.commit()
