import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from telegram_rutor_bot.db.users import (
    get_or_create_user_by_chat_id,
    get_user,
    get_user_by_chat,
    update_user_info,
    grant_access,
    get_all_users,
    set_user_language
)
from telegram_rutor_bot.db.models import User

@pytest.mark.asyncio
async def test_user_lifecycle_db(async_session: AsyncSession):
    user = await get_or_create_user_by_chat_id(async_session, 123, name="N", username="U")
    assert user.chat_id == 123
    
    await update_user_info(async_session, user.id, name="N2")
    await async_session.refresh(user)
    assert user.name == "N2"
    
    await grant_access(async_session, 123)
    await async_session.refresh(user)
    assert user.is_authorized is True
    
    await set_user_language(async_session, 123, "ru")
    await async_session.refresh(user)
    assert user.language == "ru"
    
    all_u = await get_all_users(async_session)
    assert len(all_u) >= 1
