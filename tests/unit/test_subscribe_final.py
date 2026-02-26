from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.handlers.subscribe import subscribe, subscriptions_list, unsubscribe


@pytest.mark.asyncio
async def test_all_subscribe_handlers(mocker):
    mock_user = MagicMock(id=1, is_authorized=True, language='en')
    mocker.patch('telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id', AsyncMock(return_value=mock_user))
    mocker.patch('telegram_rutor_bot.handlers.subscribe.get_user_by_chat', AsyncMock(return_value=mock_user))

    # Mock DB
    mocker.patch('telegram_rutor_bot.handlers.subscribe.db_subscribe', AsyncMock(return_value=(True, 'OK')))
    mocker.patch('telegram_rutor_bot.handlers.subscribe.db_unsubscribe', AsyncMock(return_value=True))
    mocker.patch('telegram_rutor_bot.handlers.subscribe.get_subscriptions', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.handlers.subscribe.get_async_session')

    update = MagicMock()
    update.effective_chat.id = 123
    update.message.text = '/subscribe_1'
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await subscribe(update, context)
    update.message.text = '/unsubscribe_1'
    await unsubscribe(update, context)
    await subscriptions_list(update, context)

    assert context.bot.send_message.called
