from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.services.monitor import WatchlistMonitor


@pytest.mark.asyncio
async def test_notify_users_found_items_v2(mocker):
    mock_session = AsyncMock()

    # Mock film with torrents
    mock_torrent = MagicMock(name='T1', sz=1073741824, magnet='mag')
    mock_film = MagicMock(name='F1', year=2024, torrents=[mock_torrent])

    mocker.patch('telegram_rutor_bot.services.monitor.get_films_by_ids', AsyncMock(return_value=[mock_film]))

    monitor = WatchlistMonitor(mock_session)
    monitor._send_notification_to_all_users = AsyncMock()

    bot = AsyncMock()
    await monitor._notify_users_about_found_items(bot, [1], 'T1')
    assert monitor._send_notification_to_all_users.called
