import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, Message, User as TgUser
from telegram_rutor_bot.handlers.search import search_list, search_delete, search_execute

@pytest.fixture
def tg_update():
    u = MagicMock(spec=Update)
    u.effective_chat = MagicMock(id=123)
    u.message = MagicMock(spec=Message)
    u.message.reply_text = AsyncMock()
    u.callback_query = MagicMock()
    u.callback_query.answer = AsyncMock()
    return u

@pytest.fixture
def mock_db_user():
    return MagicMock(id=1, is_authorized=True, is_admin=True, language="en")

@pytest.fixture(autouse=True)
def mock_sec(mocker, mock_db_user):
    mocker.patch("telegram_rutor_bot.utils.security.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock()))
    mocker.patch("telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id", AsyncMock(return_value=mock_db_user))
    # Handlers deps
    mocker.patch("telegram_rutor_bot.handlers.search.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock()))
    mocker.patch("telegram_rutor_bot.handlers.search.get_user_by_chat", AsyncMock(return_value=mock_db_user))

@pytest.mark.asyncio
async def test_handlers_basic(mocker, tg_update):
    mocker.patch("telegram_rutor_bot.handlers.search.get_searches", AsyncMock(return_value=[]))
    await search_list(tg_update, MagicMock())
    assert tg_update.message.reply_text.called
    
    tg_update.message.text = "/ds_1"
    mocker.patch("telegram_rutor_bot.handlers.search.delete_search", AsyncMock())
    await search_delete(tg_update, MagicMock())
    assert tg_update.message.reply_text.called
