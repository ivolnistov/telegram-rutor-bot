import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from telegram_rutor_bot.db.searches import (
    add_search_to_db,
    update_search,
    get_search,
    get_searches,
    get_search_subscribers,
    update_last_success,
    delete_search,
    get_searches_by_user,
    get_categories,
    create_category,
    update_category,
    delete_category
)
from telegram_rutor_bot.db.models import User, Search, Category

@pytest.mark.asyncio
async def test_search_lifecycle_db(async_session: AsyncSession):
    user = User(chat_id=123, is_authorized=True)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    # create_category
    cat = await create_category(async_session, "Movies", icon="M", folder="/f")
    assert cat.id is not None
    
    # add_search
    sid = await add_search_to_db(async_session, "http://t", "0 0 * * *", user.id, category="Movies")
    assert sid is not None
    
    # get_search
    s = await get_search(async_session, sid)
    assert s.url == "http://t"
    
    # update_search
    await update_search(async_session, sid, url="http://u", cron="1 1 * * *")
    await async_session.refresh(s)
    assert s.url == "http://u"
    
    # update_last_success
    await update_last_success(async_session, sid)
    await async_session.refresh(s)
    assert s.last_success is not None
    
    # delete_category
    await delete_category(async_session, cat.id)
    
    # delete_search
    await delete_search(async_session, sid)
    assert await get_search(async_session, sid) is None

@pytest.mark.asyncio
async def test_get_searches_filtering_db(async_session: AsyncSession):
    s1 = Search(url="s1", cron="* * * * *", creator_id=None)
    async_session.add(s1)
    await async_session.commit()
    
    res = await get_searches(async_session, show_empty=False)
    assert len(res) >= 1
