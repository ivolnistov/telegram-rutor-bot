from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Update

from telegram_rutor_bot.handlers.torrents import torrent_download, torrent_list


@pytest.mark.asyncio
async def test_torrent_list_simple(mocker):
    update = MagicMock(spec=Update)
    update.effective_chat.id = 123
    update.effective_user.id = 123

    mock_user = MagicMock()
    mock_user.is_authorized = True
    mock_user.language = 'en'

    mocker.patch('telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id', AsyncMock(return_value=mock_user))
    mocker.patch('telegram_rutor_bot.handlers.torrents.get_user_by_chat', AsyncMock(return_value=mock_user))

    # Mock DB returns empty
    mocker.patch('telegram_rutor_bot.handlers.torrents.get_films', AsyncMock(return_value=[]))

    # Mock session
    mocker.patch(
        'telegram_rutor_bot.handlers.torrents.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock()),
    )

    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await torrent_list(update, context)
    assert context.bot.send_message.called


@pytest.mark.asyncio
async def test_torrent_download_simple(mocker):
    update = MagicMock()
    update.message.text = '/dl_1'
    update.effective_chat.id = 123

    mock_user = MagicMock(is_authorized=True, language='en')
    mocker.patch('telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id', AsyncMock(return_value=mock_user))
    mocker.patch('telegram_rutor_bot.handlers.torrents.get_user_by_chat', AsyncMock(return_value=mock_user))

    mock_torrent = MagicMock(id=1, name='T1')
    mocker.patch('telegram_rutor_bot.handlers.torrents.get_torrent_by_id', AsyncMock(return_value=mock_torrent))
    mocker.patch('telegram_rutor_bot.handlers.torrents.download_torrent', AsyncMock())

    mocker.patch('telegram_rutor_bot.handlers.torrents.get_async_session')

    context = MagicMock()
    update.message.reply_text = AsyncMock()

    await torrent_download(update, context)
    assert update.message.reply_text.called
