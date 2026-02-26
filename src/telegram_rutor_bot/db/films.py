"""Film operations for movie metadata"""

import contextlib

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
    original_title: str | None = None,
    country: str | None = None,
) -> Film:
    """Get existing film or create new one"""
    # Try to get existing film
    result = await session.execute(select(Film).where(Film.blake == blake))
    film = result.scalar_one_or_none()

    if film:
        # Update fields if provided
        fields = {
            'year': year,
            'name': name,
            'ru_name': ru_name,
            'poster': poster,
            'rating': str(rating) if rating is not None else None,
            'category_id': category_id,
            'original_title': original_title,
            'country': country,
        }
        updated = False
        for k, v in fields.items():
            if v is not None and not getattr(film, k):
                setattr(film, k, v)
                updated = True

        if updated:
            await session.commit()
        return film

    # Create new film
    new_film = Film(
        blake=blake,
        year=year,
        name=name,
        ru_name=ru_name,
        poster=poster,
        rating=str(rating) if rating is not None else None,
        category_id=category_id,
        original_title=original_title,
        country=country,
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

    stmt = (
        select(Film)
        .options(selectinload(Film.torrents))
        .where(Film.rating.is_not(None))
        .order_by(func.random())  # pylint: disable=not-callable
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
    original_title: str | None = None,
    kp_rating: float | str | None = None,
) -> bool:
    """Update film metadata"""
    result = await session.execute(select(Film).where(Film.id == film_id))
    film = result.scalar_one_or_none()

    if not film:
        return False

    # Standard updates
    for attr, value in {
        'tmdb_id': tmdb_id,
        'tmdb_media_type': tmdb_media_type,
        'year': year,
        'name': name,
        'ru_name': ru_name,
        'poster': poster,
        'country': country,
        'genres': genres,
        'original_title': original_title,
    }.items():
        if value is not None:
            setattr(film, attr, value)

    # Special cases
    if rating is not None:
        film.rating = str(rating)

    if kp_rating is not None:
        with contextlib.suppress(ValueError, TypeError):
            film.kp_rating = float(kp_rating)

    await session.commit()
    return True


async def get_unlinked_films(session: AsyncSession, limit: int = 100) -> list[Film]:
    """Get films that lack TMDB link"""
    # Assuming unlinked means tmdb_id is NULL
    result = await session.execute(select(Film).where(Film.tmdb_id.is_(None)).limit(limit))
    return list(result.scalars().all())
