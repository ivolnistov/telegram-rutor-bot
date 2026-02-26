from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from telegram_rutor_bot.web.app import app
from telegram_rutor_bot.web.auth import get_current_admin_user

client = TestClient(app)


@pytest.fixture
def mock_admin():
    u = MagicMock()
    u.id = 1
    u.is_admin = True
    u.is_authorized = True
    return u


def test_app_all_get_endpoints(mocker, mock_admin):
    app.dependency_overrides[get_current_admin_user] = lambda: mock_admin

    # Session mock
    mock_session = AsyncMock()
    # scalars().all() -> returns []
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)

    mocker.patch(
        'telegram_rutor_bot.web.app.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()),
    )

    # Mock specific functions to return list
    mocker.patch('telegram_rutor_bot.web.app.get_searches', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.web.app.get_all_users', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.web.app.get_categories', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.web.app.get_recent_torrents', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.web.app.get_films', AsyncMock(return_value=[]))

    mock_tc = AsyncMock()
    mock_tc.list_torrents.return_value = []
    mocker.patch('telegram_rutor_bot.web.app.get_torrent_client', return_value=mock_tc)

    # Test all GETs
    client.get('/api/health')
    client.get('/api/searches')
    client.get('/api/users')
    client.get('/api/categories')
    client.get('/api/torrents')
    client.get('/api/films')
    client.get('/api/tasks')
    client.get('/api/downloads')
    client.get('/api/settings')

    app.dependency_overrides = {}
