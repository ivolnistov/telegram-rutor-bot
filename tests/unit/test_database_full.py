from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.db.database import db_state, get_async_session, init_db


def test_init_db_multiple_times(mocker):
    mocker.patch('telegram_rutor_bot.db.database.create_async_engine')
    mocker.patch('telegram_rutor_bot.db.database.async_sessionmaker')

    # Reset state
    db_state.engine = None
    db_state.session_maker = None

    init_db()
    assert db_state.engine is not None

    engine1 = db_state.engine
    init_db()
    assert db_state.engine is engine1  # Should not re-create if already set


@pytest.mark.asyncio
async def test_get_async_session_error():
    db_state.session_maker = None
    with pytest.raises(RuntimeError):
        async with get_async_session():
            pass


@pytest.mark.asyncio
async def test_get_async_session_success(mocker):
    mock_maker = MagicMock()
    mock_maker.return_value = AsyncMock()
    db_state.session_maker = mock_maker

    async with get_async_session() as session:
        assert session is not None
