import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.tasks.jobs import _run_search_process
from telegram_rutor_bot.db.models import TaskExecution, Search

@pytest.mark.asyncio
async def test_run_search_process_success_v2(mocker):
    mock_session = AsyncMock()
    mock_task = MagicMock()
    mock_task.progress = 0
    
    mock_search = MagicMock(spec=Search, id=1, url="http://t", query="q", category_id=1)
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_search", AsyncMock(return_value=mock_search))
    
    mocker.patch("telegram_rutor_bot.tasks.jobs.parse_rutor", AsyncMock(return_value=[10, 11]))
    mocker.patch("telegram_rutor_bot.tasks.jobs.get_films_by_ids", AsyncMock(return_value=[]))
    
    # Mock subscribers - use REAL strings
    mock_sub = MagicMock()
    mock_sub.username = "User1"
    mock_sub.chat_id = 123
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_sub]
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    mocker.patch("telegram_rutor_bot.tasks.jobs.notify_subscribers", AsyncMock())
    mocker.patch("telegram_rutor_bot.tasks.jobs.update_last_success", AsyncMock())
    mocker.patch("telegram_rutor_bot.tasks.jobs.check_matches", AsyncMock())
    
    res = await _run_search_process(mock_session, mock_task, 1)
    assert "Found 2 new items" in res
    assert "User1" in res
    assert mock_session.commit.called
