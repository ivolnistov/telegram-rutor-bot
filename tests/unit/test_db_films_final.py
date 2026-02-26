import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.db.films import (
    get_films,
    get_or_create_film,
    get_recommendations,
    get_unlinked_films,
    search_films,
    update_film_metadata,
)


@pytest.mark.asyncio
async def test_film_lifecycle_db(async_session: AsyncSession):
    film = await get_or_create_film(async_session, 'blake1', year=2020, name='Film')
    assert film.id is not None

    await update_film_metadata(async_session, film.id, genres='Action', rating=8.5)
    await async_session.refresh(film)

    all_f = await get_films(async_session)
    assert len(all_f) >= 1

    search_res = await search_films(async_session, 'Film')
    assert len(search_res) >= 1

    recs = await get_recommendations(async_session)
    assert len(recs) >= 1

    unlinked = await get_unlinked_films(async_session)
    assert len(unlinked) >= 1
