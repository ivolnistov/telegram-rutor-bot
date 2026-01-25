"""Database operations for application configuration."""

from typing import TYPE_CHECKING, Unpack

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.db.models import AppConfig

if TYPE_CHECKING:
    from telegram_rutor_bot.db.models import AppConfig, AppConfigUpdate


async def get_db_config(session: AsyncSession) -> AppConfig:
    """Get application configuration."""
    result = await session.execute(select(AppConfig).where(AppConfig.id == 1))
    config = result.scalar_one_or_none()

    if not config:
        config = AppConfig(id=1, is_configured=False)
        session.add(config)
        await session.flush()

    return config


async def update_db_config(session: AsyncSession, **kwargs: Unpack[AppConfigUpdate]) -> AppConfig:
    """Update application configuration."""
    config = await get_db_config(session)

    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    await session.commit()
    await session.refresh(config)
    return config
