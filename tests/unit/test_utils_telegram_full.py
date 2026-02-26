from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Bot
from telegram.error import TelegramError

from telegram_rutor_bot.utils.telegram import send_notifications


@pytest.mark.asyncio
async def test_send_notifications_logic(mocker):
    bot = AsyncMock(spec=Bot)
    chat_id = 123

    notifications = [
        {'type': 'photo', 'media': b'data', 'caption': 'Cap 1', 'reply_markup': None},
        {'type': 'text', 'media': None, 'caption': 'Cap 2', 'reply_markup': MagicMock()},
    ]

    # Success
    await send_notifications(bot, chat_id, notifications)
    assert bot.send_photo.called
    assert bot.send_message.called

    # Error branch
    bot.send_message.side_effect = TelegramError('Fail')
    # Should not raise exception because of suppress/try-except
    await send_notifications(bot, chat_id, [{'type': 'text', 'media': None, 'caption': 'E', 'reply_markup': None}])
    assert True
