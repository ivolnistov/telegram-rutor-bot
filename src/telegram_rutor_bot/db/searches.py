"""Search related database operations"""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import CursorResult, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import count

from .models import Category, Search, TaskExecution, User, subscribes_table

_UNSET: Any = object()  # sentinel for distinguishing "not provided" from None

__all__ = (
    'add_search_to_db',
    'delete_search',
    'get_search',
    'get_search_subscribers',
    'get_searches',
    'get_searches_by_user',
    'get_subscribed_searches',
    'get_subscribed_searches',
    'update_last_success',
    'update_search',
)


async def _get_or_create_category(session: AsyncSession, name: str) -> Category:
    """Get or create a category by name"""
    result = await session.execute(select(Category).where(Category.name == name))
    category = result.scalar_one_or_none()

    if not category:
        category = Category(name=name)
        session.add(category)
        await session.flush()

    return category


async def update_search(
    session: AsyncSession,
    search_id: int,
    url: str | None = None,
    cron: str | None = None,
    category: str | None = None,
    quality_filters: str | None = _UNSET,
    translation_filters: str | None = _UNSET,
    is_series: bool | None = None,
) -> bool:
    """Update search URL or cron"""
    result = await session.execute(select(Search).where(Search.id == search_id))
    search = result.scalar_one_or_none()

    if not search:
        return False

    if url:
        search.url = url
        search.query = url  # For now, use URL as query

    if cron:
        cron_parts = cron.split()
        if len(cron_parts) != 5:
            raise ValueError('Invalid cron expression')
        search.cron = cron

    if category is not None:
        if category:
            cat_obj = await _get_or_create_category(session, category)
            search.category_id = cat_obj.id
        else:
            search.category_id = None

    if quality_filters is not _UNSET:
        search.quality_filters = quality_filters or None
    if translation_filters is not _UNSET:
        search.translation_filters = translation_filters or None

    if is_series is not None:
        search.is_series = is_series

    await session.commit()
    return True


async def add_search_to_db(
    session: AsyncSession,
    url: str,
    cron: str,
    creator_id: int,
    category: str | None = None,
    is_series: bool = False,
) -> int:
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

    category_id = None
    if category:
        cat_obj = await _get_or_create_category(session, category)
        category_id = cat_obj.id

    # Create new search
    new_search = Search(
        url=url,
        query=url,  # For now, use URL as query
        cron=' '.join(cron_parts),
        creator_id=creator_id,
        category_id=category_id,
        is_series=is_series,
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
    query = select(Search).options(selectinload(Search.category_rel))

    if not show_empty:
        # Filter out searches with no subscribers, EXCEPT system searches
        subquery = (
            select(count())
            .select_from(subscribes_table)
            .where(subscribes_table.c.search_id == Search.id)
            .scalar_subquery()
        )
        query = query.where((subquery > 0) | (Search.creator_id.is_(None)))

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
    # Delete related task executions first
    await session.execute(delete(TaskExecution).where(TaskExecution.search_id == search_id))

    # Delete subscriptions first
    await session.execute(delete(subscribes_table).where(subscribes_table.c.search_id == search_id))

    # Delete the search
    result = await session.execute(delete(Search).where(Search.id == search_id))

    await session.commit()
    return cast(CursorResult[Any], result).rowcount > 0


async def get_searches_by_user(session: AsyncSession, user_id: int) -> list[Search]:
    """Get all searches created by a user"""
    result = await session.execute(select(Search).where(Search.creator_id == user_id).order_by(Search.id))
    return list(result.scalars().all())


async def get_categories(session: AsyncSession) -> list[Category]:
    """Get all categories"""
    result = await session.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


async def create_category(
    session: AsyncSession, name: str, icon: str | None = None, folder: str | None = None
) -> Category:
    """Create a new category"""
    # Check existing
    result = await session.execute(select(Category).where(Category.name == name))
    if result.scalar_one_or_none():
        raise ValueError(f'Category {name} already exists')

    category = Category(name=name, icon=icon, folder=folder, active=True)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def update_category(
    session: AsyncSession,
    category_id: int,
    name: str | None = None,
    icon: str | None = None,
    folder: str | None = None,
    active: bool | None = None,
) -> Category | None:
    """Update a category"""
    result = await session.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()

    if not category:
        return None

    if name is not None:
        # Check uniqueness if name changed
        if name != category.name:
            existing = await session.execute(select(Category).where(Category.name == name))
            if existing.scalar_one_or_none():
                raise ValueError(f'Category {name} already exists')
        category.name = name

    if icon is not None:
        category.icon = icon
    if folder is not None:
        category.folder = folder
    if active is not None:
        category.active = active

    await session.commit()
    await session.refresh(category)
    return category


async def delete_category(session: AsyncSession, category_id: int) -> bool:
    """Delete a category"""
    # Simply delete. Searches will have category_id set to NULL if we defined cascade or not?
    # SQLAlchemy models usually need explicit cascade or nullable.
    # User didn't specify behavior. Assuming nullable=True in Search model (it is).
    result = await session.execute(delete(Category).where(Category.id == category_id))
    await session.commit()
    return cast(CursorResult[Any], result).rowcount > 0


async def get_subscribed_searches(session: AsyncSession, user_id: int) -> list[Search]:
    """Get all searches a user is subscribed to"""
    result = await session.execute(
        select(Search)
        .join(subscribes_table, Search.id == subscribes_table.c.search_id)
        .where(subscribes_table.c.user_id == user_id)
        .order_by(Search.id)
    )
    return list(result.scalars().all())
