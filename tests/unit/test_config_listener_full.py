import pytest
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from telegram_rutor_bot.config_listener import refresh_settings_from_db, config_listener_task

@pytest.mark.asyncio
async def test_refresh_settings_from_db_logic(mocker):
    # Mock DB config with all required fields to avoid AttributeErrors/KeyErrors
    mock_db_config = MagicMock()
    mock_db_config.is_configured = True
    mock_db_config.telegram_token = "db_token"
    mock_db_config.unauthorized_message = "Denied"
    mock_db_config.torrent_client = "qbittorrent"
    
    fields_to_check = [
        'telegram_token',
        'unauthorized_message',
        'torrent_client',
        'qbittorrent_host',
        'qbittorrent_port',
        'qbittorrent_username',
        'qbittorrent_password',
        'transmission_host',
        'transmission_port',
        'transmission_username',
        'transmission_password',
        'proxy',
        'seed_ratio_limit',
        'seed_time_limit',
        'inactive_seeding_time_limit',
        'tmdb_api_key',
        'tmdb_session_id',
    ]
    for field in fields_to_check:
        if not hasattr(mock_db_config, field):
            setattr(mock_db_config, field, None)
    
    mock_session = AsyncMock()
    mocker.patch("telegram_rutor_bot.config_listener.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    mocker.patch("telegram_rutor_bot.config_listener.get_db_config", AsyncMock(return_value=mock_db_config))
    
    mock_settings = mocker.patch("telegram_rutor_bot.config_listener.settings")
    
    # Test without env vars
    await refresh_settings_from_db()
    mock_settings.refresh.assert_called()
    # kwargs will have only the values that are not None
    _, kwargs = mock_settings.refresh.call_args
    assert "telegram_token" in kwargs
    assert kwargs["telegram_token"] == "db_token"

@pytest.mark.asyncio
async def test_config_listener_task_flows(mocker):
    mocker.patch("telegram_rutor_bot.config_listener.settings.redis_url", "redis://localhost")
    
    # Use a real class or a mock that supports async iteration correctly
    class MockPubSub:
        async def subscribe(self, *args, **kwargs): pass
        async def listen(self):
            yield {"type": "message", "data": "reload"}
            # Hang forever or wait to be cancelled
            while True:
                await asyncio.sleep(1)

    mock_redis = MagicMock()
    mock_redis.pubsub.return_value = MockPubSub()
    mocker.patch("telegram_rutor_bot.config_listener.Redis.from_url", return_value=mock_redis)
    
    mock_refresh = mocker.patch("telegram_rutor_bot.config_listener.refresh_settings_from_db", AsyncMock())
    
    task = asyncio.create_task(config_listener_task())
    await asyncio.sleep(0.1)
    task.cancel()
    
    assert mock_refresh.called
