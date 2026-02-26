import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.tasks.jobs import execute_search

@pytest.mark.asyncio
async def test_execute_search_error_cases(mocker):
    mocker.patch("telegram_rutor_bot.tasks.jobs.Bot", return_value=AsyncMock())
    
    # Mock search lookup
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_search", AsyncMock(return_value=MagicMock(id=1, url="http://t", last_success_from_now=lambda: 100)))
    
    # Mock session
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    
    # Trigger Exception in _run_search_process
    mocker.patch("telegram_rutor_bot.tasks.jobs._run_search_process", AsyncMock(side_effect=Exception("Generic Error")))
    
    await execute_search(1)
    assert mock_session.commit.called
