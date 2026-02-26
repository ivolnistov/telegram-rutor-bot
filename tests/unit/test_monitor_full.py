from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.db.models import Film, User
from telegram_rutor_bot.services.monitor import WatchlistMonitor


@pytest.fixture
def monitor(mocker):
    session = AsyncMock()
    m = WatchlistMonitor(session)
    # Mock TMDB
    m.tmdb = AsyncMock()
    return m


@pytest.mark.asyncio
async def test_monitor_sync_watchlist_full(mocker, monitor):
    monitor.tmdb.get_watchlist.side_effect = [
        [{'id': 1, 'title': 'M1', 'release_date': '2024-01-01', 'vote_average': 8.0, 'poster_path': 'p1'}],  # movies
        [{'id': 2, 'name': 'S1', 'first_air_date': '2024-01-01', 'vote_average': 7.5, 'poster_path': 'p2'}],  # tv
    ]

    # Use real Film object to avoid attribute issues
    mock_film = Film(tmdb_id=1, monitored=False, name='M1', blake='b1', year=2024)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.side_effect = [mock_film, None]
    monitor.session.execute.return_value = mock_result

    count = await monitor.sync_watchlist()
    assert count == 2
    assert mock_film.monitored is True


@pytest.mark.asyncio
async def test_monitor_check_monitored_items_full(mocker, monitor):
    # Mock cutoff check
    f1 = MagicMock(spec=Film)
    f1.name = 'F1'  # REAL STRING
    f1.tmdb_media_type = 'movie'
    f1.last_search = None
    f1.id = 1

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [f1]
    monitor.session.execute.return_value = mock_result

    # Mock parse_rutor
    mocker.patch('telegram_rutor_bot.services.monitor.parse_rutor', AsyncMock(return_value=[10]))

    # Mock notifications
    monitor._notify_users_about_found_items = AsyncMock()

    mocker.patch('telegram_rutor_bot.services.monitor.settings.telegram_token', 'token')
    mocker.patch('telegram_rutor_bot.services.monitor.Bot', return_value=MagicMock())

    await monitor.check_monitored_items()
    assert monitor._notify_users_about_found_items.called
    assert f1.last_search is not None


@pytest.mark.asyncio
async def test_monitor_notification_flows(mocker, monitor):
    bot = AsyncMock()

    # _send_notification_to_all_users
    u1 = MagicMock(spec=User, chat_id=123)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [u1]
    monitor.session.execute.return_value = mock_result

    await monitor._send_notification_to_all_users(bot, 'Msg')
    assert bot.send_message.called

    # _notify_users_about_found_items
    f1 = MagicMock(spec=Film, name='F1', year=2024)
    # Use real Torrent object or mock with real strings
    t1 = MagicMock(name='T1', sz=10**9, magnet='mag')
    t1.name = 'Torrent 1'  # REAL STRING
    f1.torrents = [t1]
    mocker.patch('telegram_rutor_bot.services.monitor.get_films_by_ids', AsyncMock(return_value=[f1]))

    monitor._send_notification_to_all_users = AsyncMock()
    await monitor._notify_users_about_found_items(bot, [10], 'F1')
    assert monitor._send_notification_to_all_users.called
