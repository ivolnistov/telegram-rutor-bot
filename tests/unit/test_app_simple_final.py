from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from telegram_rutor_bot.web.app import app
from telegram_rutor_bot.web.auth import get_current_admin_user

client = TestClient(app)


def test_app_simple_gets(mocker):
    # health
    res = client.get('/api/health')
    assert res.status_code == 200

    # Bypass auth for other tests
    app.dependency_overrides[get_current_admin_user] = lambda: MagicMock(is_admin=True)

    # Mock DB functions to return empty lists (simplest passing case)
    mocker.patch(
        'telegram_rutor_bot.web.app.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock()),
    )
    mocker.patch('telegram_rutor_bot.web.app.get_searches', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.web.app.get_all_users', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.web.app.get_categories', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.web.app.get_recent_torrents', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.web.app.get_films', AsyncMock(return_value=[]))

    # Hits
    client.get('/api/searches')
    client.get('/api/users')
    client.get('/api/categories')
    client.get('/api/torrents')
    client.get('/api/films')

    app.dependency_overrides = {}
