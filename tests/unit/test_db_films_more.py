import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.db.films import get_films, search_films
from telegram_rutor_bot.db.models import Film


@pytest.mark.asyncio
async def test_get_films_search_full(async_session: AsyncSession):
    f1 = Film(blake='f1', name='Action Film', year=2020, category_id=1)
    f2 = Film(blake='f2', name='Drama Film', year=2021, category_id=2)
    async_session.add_all([f1, f2])
    await async_session.commit()

    # search_films
    res = await search_films(async_session, 'Action', category_id=1)
    assert len(res) == 1
    assert res[0].name == 'Action Film'

    # get_films with limit
    res2 = await get_films(async_session, limit=1)
    assert len(res2) == 1
