"""Database operations for application configuration."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.db.models import AppConfig


async def get_db_config(session: AsyncSession) -> AppConfig:
    """Get application configuration from database.

    Creates default configuration if not exists.
    """
    stmt = select(AppConfig).where(AppConfig.id == 1)
    result = await session.execute(stmt)
    config = result.scalars().first()

    if not config:
        config = AppConfig(id=1)
        session.add(config)
        await session.commit()
        await session.refresh(config)

    return config


async def update_db_config(session: AsyncSession, **kwargs: Any) -> AppConfig:  # noqa: ANN401
    """Update application configuration."""
    config = await get_db_config(session)

    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    await session.commit()
    await session.refresh(config)
    return config
