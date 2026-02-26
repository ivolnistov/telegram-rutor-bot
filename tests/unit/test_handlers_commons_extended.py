import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.handlers.commons import start, help_handler, language_handler, set_language_callback, add_user_cmd

@pytest.mark.asyncio
async def test_start_handler(mocker):
    update = MagicMock()
    update.effective_chat.id = 123
    
    mock_user = MagicMock()
    mock_user.language = "en"
    mock_user.is_authorized = True
    mocker.patch("telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id", AsyncMock(return_value=mock_user))
    mocker.patch("telegram_rutor_bot.handlers.commons.get_or_create_user_by_chat_id", AsyncMock(return_value=mock_user))
    mocker.patch("telegram_rutor_bot.handlers.commons.get_async_session")
    
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    await start(update, context)
    assert context.bot.send_message.called

@pytest.mark.asyncio
async def test_help_handler(mocker):
    update = MagicMock()
    update.effective_chat.id = 123
    
    mock_user = MagicMock()
    mock_user.is_authorized = True
    mocker.patch("telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id", AsyncMock(return_value=mock_user))
    mocker.patch("telegram_rutor_bot.handlers.commons.get_user_by_chat", AsyncMock(return_value=mock_user))
    mocker.patch("telegram_rutor_bot.handlers.commons.get_async_session")
    
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    await help_handler(update, context)
    assert context.bot.send_message.called

@pytest.mark.asyncio
async def test_language_handler(mocker):
    update = MagicMock()
    update.effective_chat.id = 123
    
    mock_user = MagicMock()
    mock_user.is_authorized = True
    mocker.patch("telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id", AsyncMock(return_value=mock_user))
    mocker.patch("telegram_rutor_bot.handlers.commons.get_user_by_chat", AsyncMock(return_value=mock_user))
    mocker.patch("telegram_rutor_bot.handlers.commons.get_async_session")
    
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    await language_handler(update, context)
    assert context.bot.send_message.called

@pytest.mark.asyncio
async def test_set_language_callback(mocker):
    update = MagicMock()
    update.effective_chat.id = 123
    update.callback_query.data = "lang_ru"
    update.callback_query.answer = AsyncMock()
    
    mock_user = MagicMock()
    mock_user.is_authorized = True
    mocker.patch("telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id", AsyncMock(return_value=mock_user))
    mocker.patch("telegram_rutor_bot.handlers.commons.set_user_language", AsyncMock())
    mocker.patch("telegram_rutor_bot.handlers.commons.get_async_session")
    
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    await set_language_callback(update, context)
    assert update.callback_query.answer.called
    assert context.bot.send_message.called

@pytest.mark.asyncio
async def test_add_user_cmd_success(mocker):
    update = MagicMock()
    update.effective_chat.id = 123
    
    mock_user = MagicMock()
    mock_user.is_authorized = True
    mocker.patch("telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id", AsyncMock(return_value=mock_user))
    mocker.patch("telegram_rutor_bot.handlers.commons.get_user_by_chat", AsyncMock(return_value=mock_user))
    mocker.patch("telegram_rutor_bot.handlers.commons.grant_access", AsyncMock())
    mocker.patch("telegram_rutor_bot.handlers.commons.get_async_session")
    
    context = MagicMock()
    context.args = ["456"]
    context.bot.send_message = AsyncMock()
    
    await add_user_cmd(update, context)
    assert context.bot.send_message.called
    assert "456" in context.bot.send_message.call_args[1]["text"]
