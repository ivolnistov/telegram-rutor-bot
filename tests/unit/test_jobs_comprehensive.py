from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.db.models import TaskExecution
from telegram_rutor_bot.tasks.jobs import (
    _resolve_search_task,
)


@pytest.mark.asyncio
async def test_resolve_search_task_scenarios(mocker):
    mock_session = AsyncMock()
    bot = AsyncMock()

    # Case 1: Cancelled task
    mock_task = MagicMock(spec=TaskExecution, status='cancelled')
    mock_session.get.return_value = mock_task
    res = await _resolve_search_task(mock_session, 1, 100, bot, 123)
    assert res is None
    assert bot.send_message.called

    # Case 2: Pending task exists
    mock_task.status = 'pending'
    mock_session.get.return_value = None
    mock_result = MagicMock()
    # Mock chain: session.execute(stmt).scalars().first()
    mock_result.scalars.return_value.first.return_value = mock_task
    mock_session.execute.return_value = mock_result
    res2 = await _resolve_search_task(mock_session, 1, None, bot, None)
    assert res2 == mock_task
    assert res2.status == 'running'

    # Case 3: Already running
    # Second call to execute (stmt_running)
    mock_result_running = MagicMock()
    mock_result_running.scalars.return_value.first.return_value = MagicMock(status='running')
    # First call (stmt_pending) returns None
    mock_result_pending = MagicMock()
    mock_result_pending.scalars.return_value.first.return_value = None

    mock_session.execute.side_effect = [mock_result_pending, mock_result_running]
    res3 = await _resolve_search_task(mock_session, 1, None, bot, None)
    assert res3 is None
