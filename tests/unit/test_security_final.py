from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.utils.security import security


@pytest.mark.asyncio
async def test_security_unauthorized_full(mocker):
    # Mock user NOT authorized
    mock_user = MagicMock(is_authorized=False)
    mocker.patch('telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id', AsyncMock(return_value=mock_user))
    mocker.patch('telegram_rutor_bot.utils.security.settings.unauthorized_message', 'Denied')

    update = MagicMock()
    update.effective_chat.id = 123
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    @security()
    async def handler(u, c):
        return 'OK'

    res = await handler(update, context)
    assert res is None
    assert context.bot.send_message.called
    assert context.bot.send_message.call_args[1]['text'] == 'Denied'
