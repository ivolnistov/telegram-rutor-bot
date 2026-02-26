from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.tasks.jobs import execute_search


@pytest.mark.asyncio
async def test_execute_search_full_cycle(mocker):
    # Mock settings/Bot
    mocker.patch('telegram_rutor_bot.tasks.jobs.Bot', return_value=AsyncMock())

    # Mock search
    mock_search = MagicMock(id=1, url='http://t', query='q')
    mock_search.last_success_from_now.return_value = 100
    mocker.patch('telegram_rutor_bot.tasks.jobs.get_search', AsyncMock(return_value=mock_search))

    # Mock session
    mock_session = AsyncMock()
    # Mock task check: no pending task
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    mocker.patch(
        'telegram_rutor_bot.tasks.jobs.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()),
    )

    # Mock _run_search_process returning success
    mocker.patch('telegram_rutor_bot.tasks.jobs._run_search_process', AsyncMock(return_value='Ok'))

    await execute_search(1)

    assert mock_session.commit.called
    # Check that task was updated
    assert mock_session.add.called
