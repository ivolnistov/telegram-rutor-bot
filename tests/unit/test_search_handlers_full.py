from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Message, Update

from telegram_rutor_bot.handlers.search import search_delete, search_list


@pytest.fixture
def tg_update():
    u = MagicMock(spec=Update)
    u.effective_chat = MagicMock(id=123)
    u.message = MagicMock(spec=Message)
    u.message.reply_text = AsyncMock()
    return u


@pytest.fixture
def mock_db_user():
    return MagicMock(id=1, is_authorized=True, is_admin=True, language='en')


@pytest.fixture(autouse=True)
def mock_sec(mocker, mock_db_user):
    mocker.patch(
        'telegram_rutor_bot.utils.security.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock()),
    )
    mocker.patch(
        'telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id', AsyncMock(return_value=mock_db_user)
    )
    mocker.patch(
        'telegram_rutor_bot.handlers.search.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock()),
    )
    mocker.patch('telegram_rutor_bot.handlers.search.get_user_by_chat', AsyncMock(return_value=mock_db_user))


@pytest.mark.asyncio
async def test_handlers_basic(mocker, tg_update):
    mocker.patch('telegram_rutor_bot.handlers.search.get_searches', AsyncMock(return_value=[]))

    mock_context = MagicMock()
    mock_context.bot = AsyncMock()
    mock_context.bot.send_message = AsyncMock()

    await search_list(tg_update, mock_context)
    # search_list uses bot.send_message
    assert mock_context.bot.send_message.called

    tg_update.message.text = '/ds_1'
    mocker.patch('telegram_rutor_bot.handlers.search.delete_search', AsyncMock())
    await search_delete(tg_update, mock_context)
    # search_delete uses bot.send_message
    assert mock_context.bot.send_message.called
