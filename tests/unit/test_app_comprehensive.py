from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from telegram_rutor_bot.db.database import db_state
from telegram_rutor_bot.db.models import User
from telegram_rutor_bot.web.app import app
from telegram_rutor_bot.web.auth import get_current_admin_user, get_current_user

client = TestClient(app)


@pytest.fixture
def mock_admin():
    return User(id=1, chat_id=123, username='admin', is_admin=True, is_authorized=True)


@pytest.fixture(autouse=True)
def bypass_auth(mocker, mock_admin):
    app.dependency_overrides[get_current_admin_user] = lambda: mock_admin
    app.dependency_overrides[get_current_user] = lambda: mock_admin

    # Initialize DB globally for these tests
    db_state.session_maker = MagicMock(
        return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock())
    )

    yield
    app.dependency_overrides = {}
    db_state.session_maker = None


def test_app_health(mocker):
    mocker.patch('telegram_rutor_bot.web.app.init_db')
    mocker.patch('telegram_rutor_bot.web.app.broker.startup', AsyncMock())
    res = client.get('/api/health')
    assert res.status_code == 200


def test_app_searches(mocker):
    mocker.patch('telegram_rutor_bot.web.app.get_searches', AsyncMock(return_value=[]))
    assert client.get('/api/searches').status_code == 200


def test_app_films_update(mocker):
    mock_film = MagicMock(spec=['id', 'user_rating'])
    mock_film.id = 1
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_film
    mock_session.execute.return_value = mock_result
    mocker.patch(
        'telegram_rutor_bot.web.app.get_async_session',
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_session),
            __aexit__=AsyncMock(return_value=False),
        ),
    )
    res = client.put('/api/films/1', data={'user_rating': 5})
    assert res.status_code == 200


def test_app_user_status(mocker):
    mock_user = User(id=1, chat_id=123, is_authorized=True, is_admin=True, is_tfa_enabled=False, language='en')
    mock_session = AsyncMock()
    mocker.patch('telegram_rutor_bot.web.app.get_user', AsyncMock(return_value=mock_user))
    mocker.patch(
        'telegram_rutor_bot.web.app.get_async_session',
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_session),
            __aexit__=AsyncMock(return_value=False),
        ),
    )
    res = client.patch('/api/users/1/status', data={'is_authorized': 'true'})
    assert res.status_code == 200


def test_app_downloads(mocker):
    mock_tc = AsyncMock()
    mock_tc.list_torrents.return_value = []
    mocker.patch('telegram_rutor_bot.web.app.get_torrent_client', return_value=mock_tc)
    mocker.patch('telegram_rutor_bot.web.app._execute_torrent_action', AsyncMock(return_value={'status': 'ok'}))

    assert client.get('/api/downloads').status_code == 200
    assert client.post('/api/downloads/hash/pause').status_code == 200
