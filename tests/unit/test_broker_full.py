import pytest
from unittest.mock import AsyncMock, MagicMock
from taskiq import TaskiqState
from telegram_rutor_bot.tasks.broker import startup, shutdown

@pytest.mark.asyncio
async def test_broker_startup_flow(mocker):
    mocker.patch("telegram_rutor_bot.tasks.broker.init_db")
    
    mock_session = AsyncMock()
    mocker.patch("telegram_rutor_bot.tasks.broker.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    
    state = MagicMock(spec=TaskiqState)
    await startup(state)
    
    assert mock_session.execute.called
    assert mock_session.commit.called

@pytest.mark.asyncio
async def test_broker_shutdown_flow():
    state = MagicMock(spec=TaskiqState)
    await shutdown(state)
    assert True
