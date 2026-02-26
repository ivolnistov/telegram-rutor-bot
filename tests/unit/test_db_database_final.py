from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.db.database import db_state, get_async_db, init_db


def test_init_db_full_v3(mocker):
    mocker.patch('telegram_rutor_bot.db.database.settings.database_url', 'sqlite+aiosqlite:///test.db')
    mock_engine = MagicMock()
    mocker.patch('telegram_rutor_bot.db.database.create_async_engine', return_value=mock_engine)
    mock_sm = MagicMock()
    mocker.patch('telegram_rutor_bot.db.database.async_sessionmaker', return_value=mock_sm)
    # Reset state so init_db() runs fresh
    db_state.engine = None
    db_state.session_maker = None
    init_db()
    assert db_state.session_maker == mock_sm


@pytest.mark.asyncio
async def test_get_async_db_full():
    mock_session = AsyncMock()
    # Mock the context manager returned by session_maker()
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock()

    mock_sm = MagicMock(return_value=mock_cm)
    db_state.session_maker = mock_sm

    async for db in get_async_db():
        assert db == mock_session
        break
