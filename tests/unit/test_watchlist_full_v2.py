from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.db.models import Film, Torrent
from telegram_rutor_bot.services.watchlist import (
    _download_best_torrent_for_film,
    _find_relevant_torrents,
    check_matches,
    select_best_torrent,
)


@pytest.fixture
def mock_film():
    f = Film(name='Matrix', original_title='The Matrix', year=1999, blake='b1')
    f.max_size_gb = None
    f.min_size_gb = None
    f.voiceover_filter = None
    f.target_size_gb = None
    f.tmdb_id = 123
    return f


def test_select_best_torrent_full(mock_film):
    today = datetime.now(UTC).date()
    t1 = Torrent(name='Matrix 1080p', sz=10**10, film_id=1, magnet='m1', blake='bl1', created=today, link='l1')
    t2 = Torrent(name='Matrix 4K', sz=5 * 10**10, film_id=1, magnet='m2', blake='bl2', created=today, link='l2')

    # Minimal size (default)
    res = select_best_torrent([t1, t2], mock_film)
    assert res == t1

    # Max size constraint
    mock_film.max_size_gb = 20.0
    res2 = select_best_torrent([t1, t2], mock_film)
    assert res2 == t1

    # Min size constraint
    mock_film.max_size_gb = None
    mock_film.min_size_gb = 60.0
    res3 = select_best_torrent([t1, t2], mock_film)
    assert res3 is None

    # Voiceover filter
    mock_film.min_size_gb = None
    mock_film.voiceover_filter = 'LostFilm'
    today = datetime.now(UTC).date()
    t3 = Torrent(name='Matrix LostFilm', sz=10**10, film_id=1, magnet='m3', blake='bl3', created=today, link='l3')
    res4 = select_best_torrent([t1, t3], mock_film)
    assert res4 == t3

    # Target size
    mock_film.voiceover_filter = None
    mock_film.target_size_gb = 45.0
    res5 = select_best_torrent([t1, t2], mock_film)
    assert res5 == t2


def test_find_relevant_torrents_full(mock_film):
    today = datetime.now(UTC).date()
    t1 = Torrent(name='The Matrix Bluray', sz=10**9, film_id=1, magnet='m', blake='bl1', created=today, link='l1')
    t2 = Torrent(name='Avatar', sz=10**9, film_id=1, magnet='m2', blake='bl2', created=today, link='l2')

    res = _find_relevant_torrents(mock_film, [t1, t2])
    assert len(res) == 1
    assert res[0] == t1


@pytest.mark.asyncio
async def test_download_best_torrent_for_film_full(mocker, mock_film):
    t1 = MagicMock(spec=Torrent, name='The Matrix', magnet='mag1')
    mocker.patch('telegram_rutor_bot.services.watchlist._find_relevant_torrents', return_value=[t1])
    mocker.patch('telegram_rutor_bot.services.watchlist.select_best_torrent', return_value=t1)

    mock_tc = AsyncMock()
    mocker.patch('telegram_rutor_bot.services.watchlist.get_torrent_client', return_value=mock_tc)

    mock_session = AsyncMock()
    await _download_best_torrent_for_film(mock_session, mock_film, [t1])

    assert mock_tc.add_torrent.called
    assert mock_film.watch_status == 'downloaded'


@pytest.mark.asyncio
async def test_check_matches_full(mocker):
    mock_session = AsyncMock()
    t1 = MagicMock(spec=Torrent)

    f1 = MagicMock(spec=Film, watch_status='watching')
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [f1]
    mock_session.execute.return_value = mock_result

    mocker.patch('telegram_rutor_bot.services.watchlist._download_best_torrent_for_film', AsyncMock())

    await check_matches(mock_session, [t1])
    assert True
