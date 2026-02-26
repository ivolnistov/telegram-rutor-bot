import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.db.models import User
from telegram_rutor_bot.db.searches import (
    add_search_to_db,
    create_category,
    delete_category,
    delete_search,
    get_categories,
    get_search,
    get_searches,
    update_category,
    update_search,
)


@pytest.mark.asyncio
async def test_search_lifecycle_db(async_session: AsyncSession):
    user = User(chat_id=123, is_authorized=True)
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    # create_category
    cat = await create_category(async_session, 'Movies', icon='M', folder='/f')
    assert cat.id is not None

    # update_category
    updated_cat = await update_category(async_session, cat.id, name='Films', active=False)
    assert updated_cat.name == 'Films'

    # add_search
    sid = await add_search_to_db(async_session, 'http://t', '0 0 * * *', user.id, category='Films')
    assert sid is not None

    # get_search
    s = await get_search(async_session, sid)
    assert s.url == 'http://t'

    # update_search
    await update_search(async_session, sid, url='http://u')
    await async_session.refresh(s)
    assert s.url == 'http://u'

    # get_searches
    res = await get_searches(async_session, show_empty=True)
    assert len(res) >= 1

    # delete_search
    await delete_search(async_session, sid)
    assert await get_search(async_session, sid) is None

    # delete_category
    await delete_category(async_session, cat.id)
    assert await get_categories(async_session) == []
