import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.services.monitor import WatchlistMonitor

@pytest.mark.asyncio
async def test_sync_watchlist_v4(mocker):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    monitor = WatchlistMonitor(mock_session)
    monitor.tmdb = MagicMock()
    monitor.tmdb.get_watchlist = AsyncMock(side_effect=[
        [{"id": 1, "title": "M1", "release_date": "2024", "vote_average": 8}],
        []
    ])
    
    await monitor.sync_watchlist()
    assert mock_session.commit.called

@pytest.mark.asyncio
async def test_check_monitored_items_v4(mocker):
    mock_session = AsyncMock()
    # Film to check - use REAL string for name
    mock_film = MagicMock()
    mock_film.id = 1
    mock_film.name = "Matrix"
    mock_film.tmdb_id = 100
    mock_film.tmdb_media_type = "movie"
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_film]
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    monitor = WatchlistMonitor(mock_session)
    
    mocker.patch("telegram_rutor_bot.services.monitor.parse_rutor", AsyncMock(return_value=[1]))
    monitor._notify_users_about_found_items = AsyncMock()
    
    mocker.patch("telegram_rutor_bot.services.monitor.Bot")
    mocker.patch("telegram_rutor_bot.services.monitor.settings.telegram_token", "token")
    
    await monitor.check_monitored_items()
    assert monitor._notify_users_about_found_items.called
