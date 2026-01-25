from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.db.database import get_async_db
from telegram_rutor_bot.db.models import AppConfig, User
from telegram_rutor_bot.web.auth import get_current_user

router = APIRouter(prefix='/api/config', tags=['config'])


class SearchFilters(BaseModel):
    quality: str | None = None
    translation: str | None = None


@router.get('/filters')
async def get_filters(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    result = await db.execute(select(AppConfig).where(AppConfig.id == 1))
    config = result.scalar_one_or_none()
    return {
        'quality': config.search_quality_filters if config else None,
        'translation': config.search_translation_filters if config else None,
    }


@router.post('/filters')
async def update_filters(
    filters: SearchFilters,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, str]:
    await db.execute(
        update(AppConfig)
        .where(AppConfig.id == 1)
        .values(search_quality_filters=filters.quality, search_translation_filters=filters.translation)
    )
    await db.commit()
    return {'status': 'success'}
