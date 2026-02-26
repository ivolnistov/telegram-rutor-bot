from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from telegram_rutor_bot.db.database import db_state
from telegram_rutor_bot.db.models import User
from telegram_rutor_bot.web.app import app
from telegram_rutor_bot.web.auth import get_current_admin_if_configured

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_db():
    mock_admin = User(id=1, chat_id=123, username='admin', is_admin=True, is_authorized=True)
    app.dependency_overrides[get_current_admin_if_configured] = lambda: mock_admin
    db_state.session_maker = MagicMock(
        return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock())
    )
    yield
    app.dependency_overrides = {}
    db_state.session_maker = None


def test_get_config_unauthorized(mocker):
    mock_config = MagicMock(
        telegram_token='tok',
        torrent_client='qbittorrent',
        qbittorrent_host='localhost',
        qbittorrent_port=8080,
        qbittorrent_username='u',
        qbittorrent_password='p',
        transmission_host='',
        transmission_port=9091,
        transmission_username='',
        transmission_password='',
        proxy='',
        tmdb_api_key='',
        tmdb_session_id='',
        unauthorized_message='',
        search_quality_filters='',
        search_translation_filters='',
        seed_ratio_limit=0,
        seed_time_limit=0,
        inactive_seeding_time_limit=0,
        is_configured=True,
    )
    mocker.patch('telegram_rutor_bot.web.config_api.get_db_config', AsyncMock(return_value=mock_config))
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    mocker.patch(
        'telegram_rutor_bot.web.config_api.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()),
    )
    response = client.get('/api/config')
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_save_config_mock(mocker):
    mocker.patch('telegram_rutor_bot.web.config_api.update_db_config', new_callable=AsyncMock)
    mocker.patch('telegram_rutor_bot.web.config_api._init_users', new_callable=AsyncMock)
    mocker.patch('telegram_rutor_bot.web.config_api._save_system_searches', new_callable=AsyncMock)
    mocker.patch('telegram_rutor_bot.web.config_api._update_qbittorrent_prefs', new_callable=AsyncMock)

    payload = {
        'telegram': {'token': '123:abc', 'initial_users': []},
        'torrent': {'client': 'qbittorrent', 'host': 'localhost', 'port': 8080, 'username': 'u', 'password': 'p'},
        'searches': [],
    }

    response = client.post('/api/config', json=payload)
    assert response.status_code != 404
