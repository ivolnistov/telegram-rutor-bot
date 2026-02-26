import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.tasks.jobs import (
    notify_about_new,
    cleanup_torrents,
    execute_scheduled_searches
)

@pytest.mark.asyncio
async def test_notify_about_new_full(mocker):
    mocker.patch("telegram_rutor_bot.tasks.jobs.settings.telegram_token", "token")
    mocker.patch("telegram_rutor_bot.tasks.jobs.Bot", return_value=AsyncMock())
    
    mock_session = AsyncMock()
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    
    # Mock search and subscribers
    mock_search = MagicMock(id=1, creator_id=1, url="http://test")
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_search", AsyncMock(return_value=mock_search))
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_user", AsyncMock(return_value=MagicMock(id=1)))
    
    mock_sub = MagicMock(chat_id=123)
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_search_subscribers", AsyncMock(return_value=[mock_sub]))
    
    # Mock parse_rutor returning list of film IDs
    mocker.patch("telegram_rutor_bot.tasks.jobs.parse_rutor", AsyncMock(return_value=[10]))
    mocker.patch("telegram_rutor_bot.tasks.jobs.update_last_success", AsyncMock())
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_films_by_ids", AsyncMock(return_value=[]))
    mocker.patch("telegram_rutor_bot.tasks.jobs.format_films", AsyncMock(return_value=[]))
    
    await notify_about_new(1)
    assert True

@pytest.mark.asyncio
async def test_cleanup_torrents_full(mocker):
    mock_client = AsyncMock()
    mock_client.list_torrents.return_value = [{"hash": "h1", "status": "pausedup"}]
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_torrent_client", return_value=mock_client)
    
    await cleanup_torrents()
    assert mock_client.remove_torrent.called

@pytest.mark.asyncio
async def test_execute_scheduled_searches_full(mocker):
    mock_session = AsyncMock()
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    
    mock_search = MagicMock(id=1, cron="* * * * *")
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_searches", AsyncMock(return_value=[mock_search]))
    mocker.patch("telegram_rutor_bot.tasks.jobs.croniter.match", return_value=True)
    
    mock_kiq = mocker.patch("telegram_rutor_bot.tasks.jobs.execute_search.kiq", AsyncMock())
    
    await execute_scheduled_searches()
    assert mock_kiq.called
