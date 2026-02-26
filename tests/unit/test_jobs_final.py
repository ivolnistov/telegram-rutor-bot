import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.tasks.jobs import (
    execute_search,
    execute_scheduled_searches,
    cleanup_torrents,
    notify_about_new
)

@pytest.mark.asyncio
async def test_all_jobs_flows(mocker):
    # Mock settings/Bot
    mocker.patch("telegram_rutor_bot.tasks.jobs.settings.telegram_token", "t")
    mocker.patch("telegram_rutor_bot.tasks.jobs.Bot", return_value=AsyncMock())
    
    # Mock DB/Services
    mock_session = AsyncMock()
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_search", AsyncMock(return_value=MagicMock(url="http://t", cron="*", last_success_from_now=lambda: 100)))
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_searches", AsyncMock(return_value=[]))
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_search_subscribers", AsyncMock(return_value=[]))
    mocker.patch("telegram_rutor_bot.tasks.jobs._run_search_process", AsyncMock(return_value="Ok"))
    mocker.patch("telegram_rutor_bot.tasks.jobs.parse_rutor", AsyncMock(return_value=[]))
    
    mock_tc = AsyncMock()
    mock_tc.list_torrents.return_value = []
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_torrent_client", return_value=mock_tc)
    
    # Mock task state in DB for execute_search
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Executions
    await execute_search(1)
    await execute_scheduled_searches()
    await cleanup_torrents()
    await notify_about_new(1)
    
    assert True
