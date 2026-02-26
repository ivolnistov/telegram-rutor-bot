import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.web.config_api import _init_users, _save_system_searches
from telegram_rutor_bot.db.models import User, Search

@pytest.mark.asyncio
async def test_init_users_internal(mocker):
    mock_session = AsyncMock()
    # Mock user creation
    mocker.patch("telegram_rutor_bot.web.config_api.get_or_create_user_by_chat_id", AsyncMock(return_value=MagicMock()))
    
    # Use objects with .id attribute, not dicts
    user_data = MagicMock()
    user_data.id = 123
    user_data.username = "u"
    user_data.password = "p"
    user_data.is_tfa_enabled = False
    user_data.language = "en"
    
    await _init_users(mock_session, [user_data])
    assert mock_session.commit.called

@pytest.mark.asyncio
async def test_save_system_searches_internal(mocker):
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mocker.patch("telegram_rutor_bot.web.config_api._get_or_create_category", AsyncMock(return_value=MagicMock(id=1)))
    
    mock_search_config = MagicMock()
    mock_search_config.url = "http://t"
    mock_search_config.cron = "*"
    mock_search_config.category = None
    mock_search_config.is_series = False
    
    await _save_system_searches(mock_session, [mock_search_config])
    assert mock_session.add.called
