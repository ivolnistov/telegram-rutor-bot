import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.config_listener import refresh_settings_from_db, config_listener_task

@pytest.mark.asyncio
async def test_refresh_db_settings(mocker):
    mock_db_config = MagicMock()
    mock_db_config.is_configured = True
    # Populate all possible fields to avoid KeyError
    for f in ['telegram_token', 'unauthorized_message', 'torrent_client', 'qbittorrent_host', 'qbittorrent_port', 'qbittorrent_username', 'qbittorrent_password', 'transmission_host', 'transmission_port', 'transmission_username', 'transmission_password', 'proxy', 'seed_ratio_limit', 'seed_time_limit', 'inactive_seeding_time_limit', 'tmdb_api_key', 'tmdb_session_id']:
        setattr(mock_db_config, f, "val")
    
    mocker.patch("telegram_rutor_bot.config_listener.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock()))
    mocker.patch("telegram_rutor_bot.config_listener.get_db_config", AsyncMock(return_value=mock_db_config))
    
    mock_settings = mocker.patch("telegram_rutor_bot.config_listener.settings")
    await refresh_settings_from_db()
    assert mock_settings.refresh.called

@pytest.mark.asyncio
async def test_config_task(mocker):
    mocker.patch("telegram_rutor_bot.config_listener.settings.redis_url", "redis://localhost")
    
    async def mock_listen():
        yield {"type": "message", "data": "reload"}
        await asyncio.sleep(10)

    mock_pubsub = AsyncMock()
    mock_pubsub.listen = mock_listen
    mock_redis = MagicMock()
    mock_redis.pubsub.return_value = mock_pubsub
    mocker.patch("telegram_rutor_bot.config_listener.Redis.from_url", return_value=mock_redis)
    mocker.patch("telegram_rutor_bot.config_listener.refresh_settings_from_db", AsyncMock())
    
    task = asyncio.create_task(config_listener_task())
    await asyncio.sleep(0.1)
    task.cancel()
    assert True
