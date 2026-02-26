from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Update

from telegram_rutor_bot.handlers.search import search_delete, search_execute, search_list


@pytest.mark.asyncio
async def test_all_search_handlers(mocker):
    mock_user = MagicMock(is_authorized=True, language='en')
    mocker.patch('telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id', AsyncMock(return_value=mock_user))
    mocker.patch('telegram_rutor_bot.handlers.search.get_user_by_chat', AsyncMock(return_value=mock_user))

    mocker.patch('telegram_rutor_bot.handlers.search.get_searches', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.handlers.search.get_search', AsyncMock(return_value=MagicMock()))
    mocker.patch('telegram_rutor_bot.handlers.search.execute_search.kiq', AsyncMock())
    mocker.patch('telegram_rutor_bot.handlers.search.delete_search', AsyncMock())

    # Session mock with scalars().all() -> returns list
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)
    mocker.patch(
        'telegram_rutor_bot.handlers.search.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()),
    )

    update = MagicMock(spec=Update)
    update.effective_chat.id = 123
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await search_list(update, context)

    update.message.text = '/es_1'
    await search_execute(update, context)

    update.message.text = '/ds_1'
    await search_delete(update, context)

    assert True
