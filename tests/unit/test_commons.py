import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.handlers.commons import _get_lang

@pytest.mark.asyncio
async def test_get_lang_default(mocker):
    # Mock update
    update = MagicMock()
    update.effective_chat = None
    
    lang = await _get_lang(update)
    assert lang == "en" # Default

@pytest.mark.asyncio
async def test_get_lang_from_db(mocker):
    update = MagicMock()
    update.effective_chat.id = 123
    
    # Mock database call
    mock_get_user = mocker.patch("telegram_rutor_bot.handlers.commons.get_user_by_chat", new_callable=AsyncMock)
    mock_user = MagicMock()
    mock_user.language = "ru"
    mock_get_user.return_value = mock_user
    
    # Mock session
    mocker.patch("telegram_rutor_bot.handlers.commons.get_async_session")
    
    lang = await _get_lang(update)
    assert lang == "ru"
