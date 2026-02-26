from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.db.models import Film
from telegram_rutor_bot.db.torrents import (
    add_torrent,
    get_torrent_by_id,
    get_torrents,
    mark_torrent_downloaded,
    modify_torrent,
    search_torrents,
)


@pytest.mark.asyncio
async def test_torrent_lifecycle_db(async_session: AsyncSession):
    film = Film(blake='f1', name='F', year=2020)
    async_session.add(film)
    await async_session.commit()
    await async_session.refresh(film)

    t = await add_torrent(async_session, film.id, 'tb', 'TN', 'mag', '/l', 100, created=datetime.now(UTC))
    assert t.id is not None

    # get_torrent_by_id
    t_db = await get_torrent_by_id(async_session, t.id)
    assert t_db.name == 'TN'

    # get_torrents
    all_t = await get_torrents(async_session)
    assert len(all_t) >= 1

    # mark_torrent_downloaded
    await mark_torrent_downloaded(async_session, t.id)
    await async_session.refresh(t)
    assert t.downloaded is True

    # modify_torrent
    await modify_torrent(async_session, t.id, seeds=5)
    await async_session.refresh(t)
    assert t.seeds == 5

    # delete_search - wait, no delete_torrent here?
    # search_torrents
    res = await search_torrents(async_session, 'TN')
    assert len(res) >= 1
