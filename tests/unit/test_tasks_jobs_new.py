from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.tasks.jobs import execute_search


@pytest.mark.asyncio
async def test_execute_search_flow(mocker):
    mock_search = MagicMock(id=1, url='http://t')
    mocker.patch('telegram_rutor_bot.tasks.jobs.get_search', AsyncMock(return_value=mock_search))
    mocker.patch('telegram_rutor_bot.tasks.jobs.get_search_subscribers', AsyncMock(return_value=[]))

    mock_session = AsyncMock()
    # No pending task
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    mocker.patch(
        'telegram_rutor_bot.tasks.jobs.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()),
    )

    mocker.patch('telegram_rutor_bot.tasks.jobs._run_search_process', AsyncMock(return_value='Ok'))
    mocker.patch('telegram_rutor_bot.tasks.jobs.Bot', return_value=AsyncMock())

    await execute_search(1)
    assert mock_session.commit.called
