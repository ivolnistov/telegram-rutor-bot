"""Film operations for movie metadata"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from .models import Film

__all__ = (
    'get_films',
    'get_films_by_ids',
    'get_or_create_film',
    'update_film_metadata',
)


async def get_or_create_film(
    session: AsyncSession,
    blake: str,
    year: int | None = None,
    name: str | None = None,
    ru_name: str | None = None,
    poster: str | None = None,
    rating: float | None = None,
) -> Film:
    """Get existing film or create new one"""
    # Try to get existing film
    result = await session.execute(select(Film).where(Film.blake == blake))
    film = result.scalar_one_or_none()

    if film:
        # Update fields if provided
        if year and not film.year:
            film.year = year
        if name and not film.name:
            film.name = name
        if ru_name and not film.ru_name:
            film.ru_name = ru_name
        if poster and not film.poster:
            film.poster = poster
        if rating and not film.rating:
            film.rating = str(rating)
        await session.commit()
        return film

    # Create new film
    new_film = Film(
        blake=blake, year=year, name=name, ru_name=ru_name, poster=poster, rating=str(rating) if rating else None
    )
    session.add(new_film)
    await session.commit()
    await session.refresh(new_film)
    return new_film


async def get_films(session: AsyncSession, limit: int = 20, query: str | None = None) -> list[Film]:
    """Get films with optional query filter"""
    if query:
        # Use raw SQL for the LIKE query
        text_stmt = text(f"""
            SELECT DISTINCT f.* FROM films f
            JOIN torrents t ON f.id = t.film_id
            WHERE {query}
            ORDER BY t.created DESC
            LIMIT :limit
        """)
        result = await session.execute(text_stmt, {'limit': limit})
        return [Film(**dict(row._mapping)) for row in result]  # pylint: disable=protected-access
    # Simple query for recent films
    select_stmt = select(Film).order_by(Film.id.desc()).limit(limit)
    result = await session.execute(select_stmt)
    return list(result.scalars().all())


async def get_films_by_ids(session: AsyncSession, film_ids: list[int]) -> list[Film]:
    """Get films by list of IDs"""
    if not film_ids:
        return []

    result = await session.execute(select(Film).where(Film.id.in_(film_ids)))
    return list(result.scalars().all())


async def update_film_metadata(
    session: AsyncSession,
    film_id: int,
    year: int | None = None,
    name: str | None = None,
    ru_name: str | None = None,
    poster: str | None = None,
    rating: float | None = None,
) -> bool:
    """Update film metadata"""
    result = await session.execute(select(Film).where(Film.id == film_id))
    film = result.scalar_one_or_none()

    if not film:
        return False

    if year is not None:
        film.year = year
    if name is not None:
        film.name = name
    if ru_name is not None:
        film.ru_name = ru_name
    if poster is not None:
        film.poster = poster
    if rating is not None:
        film.rating = str(rating)

    await session.commit()
    return True
