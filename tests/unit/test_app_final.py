from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from telegram_rutor_bot.web.app import app

client = TestClient(app)


@pytest.fixture
def mock_admin():
    u = MagicMock()
    u.id = 1
    u.is_admin = True
    u.is_authorized = True
    return u


def test_web_app_endpoints(mocker, mock_admin):
    from telegram_rutor_bot.web.auth import get_current_admin_user

    app.dependency_overrides[get_current_admin_user] = lambda: mock_admin

    mocker.patch(
        'telegram_rutor_bot.web.app.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock()),
    )
    mocker.patch('telegram_rutor_bot.web.app.get_searches', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.web.app.get_all_users', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.web.app.get_categories', AsyncMock(return_value=[]))

    client.get('/api/health')
    client.get('/api/searches')
    client.get('/api/users')
    client.get('/api/categories')

    app.dependency_overrides = {}
