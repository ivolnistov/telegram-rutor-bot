import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.tasks.jobs import execute_search

@pytest.fixture
def mock_search():
    s = MagicMock()
    s.id = 1
    s.url = "http://t"
    s.query = "q"
    s.last_success_from_now.return_value = 100
    return s

@pytest.mark.asyncio
async def test_execute_search_basic(mocker, mock_search):
    # Mock session
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_search", AsyncMock(return_value=mock_search))
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_search_subscribers", AsyncMock(return_value=[]))
    
    # Mock internal search process
    mock_run = mocker.patch("telegram_rutor_bot.tasks.jobs._run_search_process", AsyncMock(return_value="Ok"))
    mocker.patch("telegram_rutor_bot.tasks.jobs.Bot", return_value=AsyncMock())
    
    await execute_search(1)
    assert mock_run.called

@pytest.mark.asyncio
async def test_execute_search_already_running(mocker, mock_search):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    # Mocking first call: pending -> None, second: running -> mock_task
    mock_result.scalars.return_value.first.side_effect = [None, MagicMock()]
    mock_session.execute = AsyncMock(return_value=mock_result)
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_search", AsyncMock(return_value=mock_search))
    mock_run = mocker.patch("telegram_rutor_bot.tasks.jobs._run_search_process", AsyncMock())
    
    await execute_search(1)
    assert not mock_run.called
