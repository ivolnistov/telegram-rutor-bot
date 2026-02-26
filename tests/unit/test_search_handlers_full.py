import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, Message, User as TgUser
from telegram.ext import ContextTypes
from telegram_rutor_bot.handlers.search import (
    search_list,
    search_delete,
    search_execute,
    search_callback_handler
)
from telegram_rutor_bot.db.models import User as DbUser, Search

@pytest.fixture
def tg_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=TgUser, id=123, username="testuser", full_name="Test")
    update.effective_chat = MagicMock(id=123)
    update.message = MagicMock(spec=Message, text="/command")
    update.message.reply_text = AsyncMock()
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    return update

@pytest.fixture
def tg_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    context.bot = AsyncMock()
    context.bot.send_message = AsyncMock()
    return context

@pytest.fixture
def mock_db_user():
    u = MagicMock(spec=DbUser)
    u.id = 1
    u.chat_id = 123
    u.is_authorized = True
    u.is_admin = True
    u.language = "en"
    return u

@pytest.fixture(autouse=True)
def mock_security(mocker, mock_db_user):
    mock_session = AsyncMock()
    mocker.patch("telegram_rutor_bot.utils.security.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    mocker.patch("telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id", AsyncMock(return_value=mock_db_user))
    
    mocker.patch("telegram_rutor_bot.handlers.search.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    mocker.patch("telegram_rutor_bot.handlers.search.get_user_by_chat", AsyncMock(return_value=mock_db_user))
    return mock_session

@pytest.mark.asyncio
async def test_search_list_v2(mocker, tg_update, tg_context, mock_db_user):
    mocker.patch("telegram_rutor_bot.handlers.search.get_searches", AsyncMock(return_value=[]))
    await search_list(tg_update, tg_context)
    assert tg_update.message.reply_text.called

@pytest.mark.asyncio
async def test_search_delete_v2(mocker, tg_update, tg_context, mock_db_user):
    tg_update.message.text = "/ds_1"
    mocker.patch("telegram_rutor_bot.handlers.search.delete_search", AsyncMock())
    await search_delete(tg_update, tg_context)
    assert tg_update.message.reply_text.called

@pytest.mark.asyncio
async def test_search_execute_v2(mocker, tg_update, tg_context, mock_db_user):
    tg_update.message.text = "/es_1"
    mock_search = MagicMock(spec=Search, id=1)
    mocker.patch("telegram_rutor_bot.handlers.search.get_search", AsyncMock(return_value=mock_search))
    mocker.patch("telegram_rutor_bot.handlers.search.execute_search", MagicMock(kiq=AsyncMock()))
    await search_execute(tg_update, tg_context)
    assert tg_update.message.reply_text.called

@pytest.mark.asyncio
async def test_search_callback_handler_v2(mocker, tg_update, tg_context, mock_db_user):
    tg_update.callback_query.data = "es_1"
    mock_search = MagicMock(spec=Search, id=1)
    mocker.patch("telegram_rutor_bot.handlers.search.get_search", AsyncMock(return_value=mock_search))
    mocker.patch("telegram_rutor_bot.handlers.search.execute_search", MagicMock(kiq=AsyncMock()))
    await search_callback_handler(tg_update, tg_context)
    assert tg_update.callback_query.answer.called
