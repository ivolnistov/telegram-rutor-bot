from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import CallbackQuery

from telegram_rutor_bot.handlers.torrents import callback_query_handler


@pytest.mark.asyncio
async def test_callback_torrents_variants(mocker):
    # Mock user
    mock_user = MagicMock(is_authorized=True, language='en')
    mocker.patch('telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id', AsyncMock(return_value=mock_user))
    mocker.patch('telegram_rutor_bot.handlers.torrents.get_user_by_chat', AsyncMock(return_value=mock_user))

    # Mock session
    mocker.patch(
        'telegram_rutor_bot.handlers.torrents.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock()),
    )

    # Mock update
    update = MagicMock()
    update.callback_query = MagicMock(spec=CallbackQuery)
    update.callback_query.answer = AsyncMock()
    update.effective_chat.id = 123

    # Mock bot
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    # CASE: dl_
    update.callback_query.data = 'dl_1'
    mocker.patch('telegram_rutor_bot.handlers.torrents.get_torrent_by_id', AsyncMock(return_value=MagicMock()))
    mocker.patch('telegram_rutor_bot.handlers.torrents.download_torrent', AsyncMock())
    await callback_query_handler(update, context)
    assert update.callback_query.answer.called

    # CASE: in_
    update.callback_query.data = 'in_1'
    mocker.patch(
        'telegram_rutor_bot.handlers.torrents.get_torrent_info', AsyncMock(return_value=('', None, [], None, {}))
    )
    await callback_query_handler(update, context)
    assert update.callback_query.answer.call_count >= 2
