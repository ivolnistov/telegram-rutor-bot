from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from telegram_rutor_bot.db.database import get_async_db
from telegram_rutor_bot.db.models import Film, User
from telegram_rutor_bot.web.app import app
from telegram_rutor_bot.web.auth import get_current_user

client = TestClient(app)


@pytest.fixture
def mock_user():
    u = User(id=1, chat_id=123, is_authorized=True, is_admin=True, username='u')
    u.name = 'User'
    u.language = 'en'
    u.is_tfa_enabled = False
    return u


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture(autouse=True)
def overrides(mock_user, mock_session):
    async def override_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_async_db] = override_db
    yield
    app.dependency_overrides = {}


def test_discovery_endpoints_extended(mocker, mock_session):
    mocker.patch('telegram_rutor_bot.api.routes.discovery.tmdb.get_trending', AsyncMock(return_value=[{'id': 1}]))
    mocker.patch('telegram_rutor_bot.api.routes.discovery.tmdb.search_multi', AsyncMock(return_value=[{'id': 2}]))
    mocker.patch('telegram_rutor_bot.api.routes.discovery.tmdb.get_recommendations', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.api.routes.discovery.tmdb.get_details', AsyncMock(return_value={'id': 3}))
    mocker.patch('telegram_rutor_bot.api.routes.discovery.tmdb.get_watchlist', AsyncMock(return_value=[]))
    mocker.patch('telegram_rutor_bot.api.routes.discovery.tmdb.add_to_watchlist', AsyncMock(return_value=True))
    mocker.patch('telegram_rutor_bot.api.routes.discovery.tmdb.rate_media', AsyncMock(return_value=True))
    mocker.patch('telegram_rutor_bot.api.routes.discovery.tmdb.delete_rating', AsyncMock(return_value=True))
    mocker.patch('telegram_rutor_bot.api.routes.discovery.tmdb.get_rated_media', AsyncMock(return_value=[]))
    mocker.patch(
        'telegram_rutor_bot.api.routes.discovery.tmdb.get_account_states', AsyncMock(return_value={'rated': 5})
    )

    mock_result = MagicMock()
    mock_result.all.return_value = [(1, 10, 8.5)]
    mock_session.execute.return_value = mock_result

    assert client.get('/api/discovery/trending').status_code == 200
    assert client.get('/api/discovery/search?q=test').status_code == 200
    assert client.get('/api/discovery/movie/1/recommendations').status_code == 200
    assert client.get('/api/discovery/movie/1').status_code == 200
    assert client.get('/api/discovery/watchlist').status_code == 200
    assert client.post('/api/discovery/watchlist?media_type=movie&media_id=1').status_code == 200
    assert (
        client.post('/api/discovery/rate', json={'media_type': 'movie', 'media_id': 1, 'value': 8.0}).status_code == 200
    )
    assert client.delete('/api/discovery/rate?media_type=movie&media_id=1').status_code == 200
    assert client.get('/api/discovery/rated').status_code == 200
    assert client.get('/api/discovery/movie/1/account_states').status_code == 200

    mock_film = MagicMock(
        spec=Film,
        id=1,
        tmdb_id=100,
        name='F',
        original_title='O',
        poster='P',
        rating=8.0,
        year=2024,
        tmdb_media_type='movie',
        country='USA',
        kp_rating=8.5,
    )
    mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_film]
    assert client.get('/api/discovery/library').status_code == 200

    mocker.patch(
        'telegram_rutor_bot.api.routes.discovery.tmdb.get_personal_recommendations', AsyncMock(return_value=[])
    )
    assert client.get('/api/discovery/personal').status_code == 200

    mocker.patch('telegram_rutor_bot.api.routes.discovery.TmdbMatcher.match_films', AsyncMock(return_value=5))
    assert client.post('/api/discovery/sync').status_code == 200

    mocker.patch('telegram_rutor_bot.api.routes.discovery.search_film_on_rutor.kiq', AsyncMock())
    mock_session.execute.return_value.scalar_one_or_none.side_effect = [None, mock_film, mock_film, mock_film]
    assert client.post('/api/discovery/search_on_rutor?media_type=movie&media_id=1').status_code == 200
