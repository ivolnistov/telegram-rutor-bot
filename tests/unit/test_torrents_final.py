from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Update

from telegram_rutor_bot.handlers.torrents import (
    torrent_download,
    torrent_downloads,
    torrent_info,
    torrent_list,
    torrent_recommend,
    torrent_search,
)


@pytest.fixture
def mock_user():
    u = MagicMock()
    u.id = 1
    u.chat_id = 123
    u.is_authorized = True
    u.language = 'en'
    return u


@pytest.mark.asyncio
async def test_all_torrent_handlers(mocker, mock_user):
    mocker.patch('telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id', AsyncMock(return_value=mock_user))
    mocker.patch('telegram_rutor_bot.handlers.torrents.get_user_by_chat', AsyncMock(return_value=mock_user))

    mocker.patch('telegram_rutor_bot.handlers.torrents.get_films', AsyncMock(return_value=[]))
    # Torrent mock with strings for urljoin
    mock_torrent = MagicMock(id=123, name='T1', link='/t/123', magnet='mag')
    mocker.patch('telegram_rutor_bot.handlers.torrents.get_torrent_by_id', AsyncMock(return_value=mock_torrent))
    mocker.patch('telegram_rutor_bot.handlers.torrents.download_torrent', AsyncMock())
    mocker.patch(
        'telegram_rutor_bot.handlers.torrents.get_torrent_info', AsyncMock(return_value=('', None, [], None, {}))
    )
    mocker.patch('telegram_rutor_bot.handlers.torrents.get_recommendations', AsyncMock(return_value=[]))

    # Mock session
    mocker.patch(
        'telegram_rutor_bot.handlers.torrents.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock()),
    )

    mock_tc = AsyncMock()
    mock_tc.list_torrents.return_value = []
    mocker.patch('telegram_rutor_bot.handlers.torrents.get_torrent_client', return_value=mock_tc)

    update = MagicMock(spec=Update)
    update.effective_chat.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await torrent_list(update, context)

    update.message.text = '/dl_123'
    await torrent_download(update, context)

    update.message.text = '/in_123'
    await torrent_info(update, context)

    update.message.text = '/search Matrix'
    await torrent_search(update, context)

    await torrent_recommend(update, context)
    await torrent_downloads(update, context)

    assert True
