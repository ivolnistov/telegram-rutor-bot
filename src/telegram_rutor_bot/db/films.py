"""Film operations for movie metadata"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import text

from .models import Film

__all__ = (
    'get_films',
    'get_films_by_ids',
    'get_or_create_film',
    'get_recommendations',
    'search_films',
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
    category_id: int | None = None,
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
        if category_id and not film.category_id:
            film.category_id = category_id
        await session.commit()
        return film

    # Create new film
    new_film = Film(
        blake=blake,
        year=year,
        name=name,
        ru_name=ru_name,
        poster=poster,
        rating=str(rating) if rating else None,
        category_id=category_id,
    )
    session.add(new_film)
    await session.commit()
    await session.refresh(new_film)
    return new_film


async def get_films(
    session: AsyncSession, limit: int = 20, query: str | None = None, category_id: int | None = None
) -> list[Film]:
    """Get films with optional query filter"""
    if query:
        # Use raw SQL for the LIKE query
        # Note: category_id filtering not implemented for raw query mode yet as it's not used by API
        text_stmt = text(f"""
            SELECT DISTINCT f.* FROM films f
            JOIN torrents t ON f.id = t.film_id
            WHERE {query}
            ORDER BY t.created DESC
            LIMIT :limit
        """)
        result = await session.execute(text_stmt, {'limit': limit})
        return [Film(**row) for row in result.mappings()]

    # Simple query for recent films
    select_stmt = select(Film).options(selectinload(Film.torrents)).order_by(Film.id.desc()).limit(limit)

    if category_id:
        select_stmt = select_stmt.where(Film.category_id == category_id)

    result = await session.execute(select_stmt)
    return list(result.scalars().all())


async def get_films_by_ids(session: AsyncSession, film_ids: list[int]) -> list[Film]:
    """Get films by list of IDs"""
    if not film_ids:
        return []

    result = await session.execute(select(Film).options(selectinload(Film.torrents)).where(Film.id.in_(film_ids)))
    return list(result.scalars().all())


async def get_recommendations(session: AsyncSession, limit: int = 5) -> list[Film]:
    """Get film recommendations (random rated films)"""
    """Get film recommendations (random rated films)"""

    stmt = (
        select(Film)
        .options(selectinload(Film.torrents))
        .where(Film.rating.is_not(None))
        .order_by(func.random())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def search_films(
    session: AsyncSession, query: str, limit: int = 20, category_id: int | None = None
) -> list[Film]:
    """Search films safely"""
    sanitized_query = f'%{query}%'
    stmt = (
        select(Film)
        .options(selectinload(Film.torrents))
        .where((Film.name.ilike(sanitized_query)) | (Film.ru_name.ilike(sanitized_query)))
    )

    if category_id:
        stmt = stmt.where(Film.category_id == category_id)

    stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_film_metadata(
    session: AsyncSession,
    film_id: int,
    year: int | None = None,
    name: str | None = None,
    ru_name: str | None = None,
    poster: str | None = None,
    rating: float | None = None,
    country: str | None = None,
    genres: str | None = None,
    tmdb_id: int | None = None,
    tmdb_media_type: str | None = None,
) -> bool:
    """Update film metadata"""
    result = await session.execute(select(Film).where(Film.id == film_id))
    film = result.scalar_one_or_none()

    if not film:
        return False

    if tmdb_id is not None:
        film.tmdb_id = tmdb_id
    if tmdb_media_type is not None:
        film.tmdb_media_type = tmdb_media_type
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
    if country is not None:
        film.country = country
    if genres is not None:
        film.genres = genres

    await session.commit()
    return True


async def get_unlinked_films(session: AsyncSession, limit: int = 100) -> list[Film]:
    """Get films that lack TMDB link"""
    # Assuming unlinked means tmdb_id is NULL
    result = await session.execute(select(Film).where(Film.tmdb_id.is_(None)).limit(limit))
    return list(result.scalars().all())
