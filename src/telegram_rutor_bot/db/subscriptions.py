"""Subscription operations for search notifications"""

from typing import Any, cast

from sqlalchemy import CursorResult, and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Search, User, subscribes_table

__all__ = (
    'get_subscriptions',
    'is_subscribed',
    'subscribe',
    'unsubscribe',
)


async def subscribe(session: AsyncSession, search_id: int, chat_id: int) -> tuple[bool, str]:
    """Subscribe a user to a search by chat_id"""
    # Get user by chat_id
    result = await session.execute(select(User).where(User.chat_id == chat_id))
    user = result.scalar_one_or_none()

    if not user:
        return False, f'User with chat_id {chat_id} not found'

    # Check if search exists
    result = await session.execute(select(Search).where(Search.id == search_id))
    search = result.scalar_one_or_none()

    if not search:
        return False, f'Search with id {search_id} not found'

    # Check if already subscribed
    result = await session.execute(
        select(subscribes_table).where(
            and_(subscribes_table.c.search_id == search_id, subscribes_table.c.user_id == user.id)
        )
    )
    if result.first():
        return False, 'Already subscribed'

    # Create subscription
    await session.execute(subscribes_table.insert().values(search_id=search_id, user_id=user.id))
    await session.commit()
    return True, 'Subscribed successfully'


async def unsubscribe(session: AsyncSession, search_id: int, user_id: int) -> bool:
    """Unsubscribe a user from a search"""
    result = await session.execute(
        delete(subscribes_table).where(
            and_(subscribes_table.c.search_id == search_id, subscribes_table.c.user_id == user_id)
        )
    )
    await session.commit()
    return cast(CursorResult[Any], result).rowcount > 0


async def get_subscriptions(session: AsyncSession, user_id: int) -> list[Search]:
    """Get all searches a user is subscribed to"""
    result = await session.execute(
        select(Search)
        .join(subscribes_table, Search.id == subscribes_table.c.search_id)
        .where(subscribes_table.c.user_id == user_id)
        .order_by(Search.id)
    )
    return list(result.scalars().all())


async def is_subscribed(session: AsyncSession, search_id: int, user_id: int) -> bool:
    """Check if a user is subscribed to a search"""
    result = await session.execute(
        select(subscribes_table).where(
            and_(subscribes_table.c.search_id == search_id, subscribes_table.c.user_id == user_id)
        )
    )
    return result.first() is not None
