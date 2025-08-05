"""Torrent operations for managing downloads"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Torrent

__all__ = (
    'add_torrent',
    'get_recent_torrents',
    'get_torrent_by_blake',
    'get_torrent_by_id',
    'get_torrent_by_magnet',
    'get_torrents',
    'get_torrents_by_film',
    'mark_torrent_downloaded',
    'modify_torrent',
)


async def add_torrent(
    session: AsyncSession,
    film_id: int,
    blake: str,
    name: str,
    magnet: str,
    link: str,
    sz: int,
    created: datetime | None = None,
    approved: bool = True,
    downloaded: bool = False,
    date: datetime | None = None,
    seeds: int | None = None,
) -> Torrent:
    """Add a new torrent"""
    # Check if torrent already exists
    result = await session.execute(select(Torrent).where(Torrent.blake == blake))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    new_torrent = Torrent(
        film_id=film_id,
        blake=blake,
        name=name,
        magnet=magnet,
        link=link,
        sz=sz,
        created=created or datetime.now(UTC),
        approved=approved,
        downloaded=downloaded,
        date=date or datetime.now(UTC),
        seeds=seeds or 0,
    )

    session.add(new_torrent)
    await session.commit()
    await session.refresh(new_torrent)
    return new_torrent


async def get_torrent_by_id(session: AsyncSession, torrent_id: int) -> Torrent | None:
    """Get torrent by ID with film info"""
    result = await session.execute(select(Torrent).options(selectinload(Torrent.film)).where(Torrent.id == torrent_id))
    return result.scalar_one_or_none()


async def get_torrents(session: AsyncSession, limit: int = 50, offset: int = 0) -> list[Torrent]:
    """Get torrents with pagination"""
    result = await session.execute(
        select(Torrent).options(selectinload(Torrent.film)).order_by(Torrent.created.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all())


async def get_torrent_by_blake(session: AsyncSession, blake: str) -> Torrent | None:
    """Get torrent by blake hash"""
    result = await session.execute(select(Torrent).options(selectinload(Torrent.film)).where(Torrent.blake == blake))
    return result.scalar_one_or_none()


async def get_torrents_by_film(session: AsyncSession, film_id: int) -> list[Torrent]:
    """Get all torrents for a film"""
    result = await session.execute(select(Torrent).where(Torrent.film_id == film_id).order_by(Torrent.created.desc()))
    return list(result.scalars().all())


async def get_torrent_by_magnet(session: AsyncSession, magnet: str) -> Torrent | None:
    """Get torrent by magnet link"""
    result = await session.execute(select(Torrent).options(selectinload(Torrent.film)).where(Torrent.magnet == magnet))
    return result.scalar_one_or_none()


async def modify_torrent(session: AsyncSession, torrent_id: int, **kwargs: str | int | bool | datetime | None) -> bool:
    """Modify torrent attributes"""
    allowed_fields = {'name', 'sz', 'approved', 'downloaded', 'seeds', 'date'}
    update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not update_data:
        return False

    result = await session.execute(update(Torrent).where(Torrent.id == torrent_id).values(**update_data))

    await session.commit()
    return result.rowcount > 0


async def get_recent_torrents(session: AsyncSession, days: int = 7, limit: int = 100) -> list[Torrent]:
    """Get torrents created in the last N days"""
    cutoff = datetime.now(UTC) - timedelta(days=days)

    result = await session.execute(
        select(Torrent)
        .options(selectinload(Torrent.film))
        .where(Torrent.created >= cutoff)
        .order_by(Torrent.created.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def mark_torrent_downloaded(session: AsyncSession, torrent_id: int) -> bool:
    """Mark torrent as downloaded"""
    result = await session.execute(update(Torrent).where(Torrent.id == torrent_id).values(downloaded=True))

    await session.commit()
    return result.rowcount > 0
