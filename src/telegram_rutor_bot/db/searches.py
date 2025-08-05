"""Search operations for scheduled rutor searches"""

from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Search, User, subscribes_table

__all__ = (
    'add_search_to_db',
    'delete_search',
    'get_search',
    'get_search_subscribers',
    'get_searches',
    'get_searches_by_user',
    'get_subscribed_searches',
    'update_last_success',
)


async def add_search_to_db(session: AsyncSession, url: str, cron: str, creator_id: int) -> int:
    """Add a new search to the database"""
    # Parse cron expression
    cron_parts = cron.split()
    if len(cron_parts) != 5:
        raise ValueError('Invalid cron expression')

    # Check if search already exists
    result = await session.execute(select(Search).where(Search.url == url))
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError(f'Search with URL {url} already exists')

    # Create new search
    new_search = Search(
        url=url,
        query=url,  # For now, use URL as query
        cron=' '.join(cron_parts),
        creator_id=creator_id,
    )

    session.add(new_search)
    await session.commit()
    await session.refresh(new_search)
    return new_search.id


async def get_search(session: AsyncSession, search_id: int) -> Search | None:
    """Get a search by ID"""
    result = await session.execute(select(Search).where(Search.id == search_id))
    return result.scalar_one_or_none()


async def get_searches(session: AsyncSession, show_empty: bool = False) -> list[Search]:
    """Get all searches"""
    query = select(Search)

    if not show_empty:
        # Filter out searches with no subscribers
        subquery = (
            select(func.count())  # pylint: disable=not-callable
            .select_from(subscribes_table)
            .where(subscribes_table.c.search_id == Search.id)
            .scalar_subquery()
        )
        query = query.where(subquery > 0)

    result = await session.execute(query.order_by(Search.id))
    return list(result.scalars().all())


async def get_search_subscribers(session: AsyncSession, search_id: int) -> list[User]:
    """Get all subscribers for a search"""
    result = await session.execute(
        select(User)
        .join(subscribes_table, User.id == subscribes_table.c.user_id)
        .where(subscribes_table.c.search_id == search_id)
    )
    return list(result.scalars().all())


async def update_last_success(session: AsyncSession, search_id: int) -> bool:
    """Update last success timestamp for a search"""
    result = await session.execute(select(Search).where(Search.id == search_id))
    search = result.scalar_one_or_none()

    if not search:
        return False

    search.last_success = datetime.now(UTC)
    await session.commit()
    return True


async def delete_search(session: AsyncSession, search_id: int) -> bool:
    """Delete a search and all its subscriptions"""
    # Delete subscriptions first
    await session.execute(delete(subscribes_table).where(subscribes_table.c.search_id == search_id))

    # Delete the search
    result = await session.execute(delete(Search).where(Search.id == search_id))

    await session.commit()
    return result.rowcount > 0


async def get_searches_by_user(session: AsyncSession, user_id: int) -> list[Search]:
    """Get all searches created by a user"""
    result = await session.execute(select(Search).where(Search.creator_id == user_id).order_by(Search.id))
    return list(result.scalars().all())


async def get_subscribed_searches(session: AsyncSession, user_id: int) -> list[Search]:
    """Get all searches a user is subscribed to"""
    result = await session.execute(
        select(Search)
        .join(subscribes_table, Search.id == subscribes_table.c.search_id)
        .where(subscribes_table.c.user_id == user_id)
        .order_by(Search.id)
    )
    return list(result.scalars().all())
