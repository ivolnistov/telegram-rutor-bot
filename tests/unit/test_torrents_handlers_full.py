import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, Message, User as TgUser
from telegram.ext import ContextTypes
from telegram_rutor_bot.handlers.torrents import (
    torrent_list,
    torrent_search,
    torrent_info,
    torrent_download,
    torrent_downloads,
    torrent_recommend,
    callback_query_handler
)
from telegram_rutor_bot.db.models import User as DbUser

@pytest.fixture
def tg_update():
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=TgUser, id=123, username="testuser", full_name="Test")
    update.effective_chat = MagicMock(id=123)
    update.message = MagicMock(spec=Message, text="/command")
    update.message.reply_text = AsyncMock()
    update.message.reply_photo = AsyncMock()
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
    
    mocker.patch("telegram_rutor_bot.handlers.torrents.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    mocker.patch("telegram_rutor_bot.handlers.torrents.get_user_by_chat", AsyncMock(return_value=mock_db_user))
    return mock_session

@pytest.mark.asyncio
async def test_torrent_list_v2(mocker, tg_update, tg_context, mock_db_user):
    mocker.patch("telegram_rutor_bot.handlers.torrents.get_films", AsyncMock(return_value=[]))
    mocker.patch("telegram_rutor_bot.handlers.torrents.send_notifications", AsyncMock())
    await torrent_list(tg_update, tg_context)
    assert tg_context.bot.send_message.called

@pytest.mark.asyncio
async def test_torrent_search_v2(mocker, tg_update, tg_context, mock_db_user):
    tg_update.message.text = "/search matrix"
    mocker.patch("telegram_rutor_bot.handlers.torrents.get_films", AsyncMock(return_value=[]))
    mocker.patch("telegram_rutor_bot.handlers.torrents.format_films", AsyncMock(return_value=[]))
    mocker.patch("telegram_rutor_bot.handlers.torrents.send_notifications", AsyncMock())
    await torrent_search(tg_update, tg_context)
    assert tg_context.bot.send_message.called

@pytest.mark.asyncio
async def test_torrent_info_v2(mocker, tg_update, tg_context, mock_db_user):
    tg_update.message.text = "/in_1"
    mocker.patch("telegram_rutor_bot.handlers.torrents.get_torrent_by_id", AsyncMock(return_value=MagicMock(link="l", name="T")))
    mocker.patch("telegram_rutor_bot.handlers.torrents.get_torrent_info", AsyncMock(return_value=("Msg", None, [], None, {})))
    await torrent_info(tg_update, tg_context)
    assert tg_update.message.reply_text.called

@pytest.mark.asyncio
async def test_torrent_download_v2(mocker, tg_update, tg_context, mock_db_user):
    tg_update.message.text = "/dl_1"
    mocker.patch("telegram_rutor_bot.handlers.torrents.get_torrent_by_id", AsyncMock(return_value=MagicMock(name="T")))
    mocker.patch("telegram_rutor_bot.handlers.torrents.download_torrent", AsyncMock())
    await torrent_download(tg_update, tg_context)
    assert tg_update.message.reply_text.called

@pytest.mark.asyncio
async def test_torrent_downloads_v2(mocker, tg_update, tg_context, mock_db_user):
    mock_client = AsyncMock()
    mock_client.list_torrents.return_value = [{"name": "T", "progress": 0.5, "status": "downloading", "size": 10**9, "download_rate": 100, "upload_rate": 100, "hash": "h"}]
    mocker.patch("telegram_rutor_bot.handlers.torrents.get_torrent_client", return_value=mock_client)
    await torrent_downloads(tg_update, tg_context)
    assert tg_context.bot.send_message.called

@pytest.mark.asyncio
async def test_torrent_recommend_v2(mocker, tg_update, tg_context, mock_db_user):
    mocker.patch("telegram_rutor_bot.handlers.torrents.get_recommendations", AsyncMock(return_value=[]))
    await torrent_recommend(tg_update, tg_context)
    assert tg_context.bot.send_message.called

@pytest.mark.asyncio
async def test_callback_query_handler_v2(mocker, tg_update, tg_context, mock_db_user):
    tg_update.callback_query.data = "dl_1"
    mocker.patch("telegram_rutor_bot.handlers.torrents.get_torrent_by_id", AsyncMock(return_value=MagicMock(name="T")))
    mocker.patch("telegram_rutor_bot.handlers.torrents.download_torrent", AsyncMock())
    await callback_query_handler(tg_update, tg_context)
    assert tg_update.callback_query.answer.called
