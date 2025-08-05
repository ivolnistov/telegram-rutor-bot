"""User operations for Telegram bot users."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User

__all__ = (
    'get_or_create_user_by_chat_id',
    'get_user',
    'get_user_by_chat',
    'update_user_info',
)


async def get_or_create_user_by_chat_id(
    session: AsyncSession, chat_id: int, name: str | None = None, username: str | None = None
) -> User:
    """Get or create user by chat ID"""
    # Try to get existing user
    result = await session.execute(select(User).where(User.chat_id == chat_id))
    user = result.scalar_one_or_none()

    if user:
        # Update name and username if provided
        if name and user.name != name:
            user.name = name
        if username and user.username != username:
            user.username = username
        await session.commit()
        return user

    # Create new user
    new_user = User(chat_id=chat_id, name=name, username=username)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """Get user by ID"""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_chat(session: AsyncSession, chat_id: int) -> User | None:
    """Get user by chat ID"""
    result = await session.execute(select(User).where(User.chat_id == chat_id))
    return result.scalar_one_or_none()


async def update_user_info(
    session: AsyncSession, user_id: int, name: str | None = None, username: str | None = None
) -> bool:
    """Update user info"""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return False

    if name is not None:
        user.name = name
    if username is not None:
        user.username = username

    await session.commit()
    return True
