import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.web.app import app
from telegram_rutor_bot.db.models import User

client = TestClient(app)

@pytest.fixture
def mock_admin_user():
    user = MagicMock(spec=User)
    user.username = "admin"
    user.is_admin = True
    user.is_authorized = True
    return user

def test_get_config_api(mocker, mock_admin_user):
    from telegram_rutor_bot.web.auth import get_current_admin_if_configured
    app.dependency_overrides[get_current_admin_if_configured] = lambda: mock_admin_user
    
    mock_db_config = MagicMock()
    mock_db_config.telegram_token = "token"
    mock_db_config.qbittorrent_password = "pass"
    mock_db_config.transmission_password = None
    mocker.patch("telegram_rutor_bot.web.config_api.get_db_config", AsyncMock(return_value=mock_db_config))
    
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    mocker.patch("telegram_rutor_bot.web.config_api.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    
    mock_client = AsyncMock()
    mock_client.get_app_preferences.return_value = {"max_ratio": 1.5}
    mocker.patch("telegram_rutor_bot.web.config_api.get_torrent_client", return_value=mock_client)
    
    response = client.get("/api/config")
    assert response.status_code == 200
    app.dependency_overrides = {}

def test_get_filters_api(mocker, mock_admin_user):
    from telegram_rutor_bot.web.auth import get_current_admin_if_configured
    app.dependency_overrides[get_current_admin_if_configured] = lambda: mock_admin_user
    
    mock_db_config = MagicMock()
    mock_db_config.search_quality_filters = "1080p"
    mock_db_config.search_translation_filters = "LostFilm"
    mocker.patch("telegram_rutor_bot.web.config_api.get_db_config", AsyncMock(return_value=mock_db_config))
    
    mock_session = AsyncMock()
    mocker.patch("telegram_rutor_bot.web.config_api.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    
    response = client.get("/api/config/filters")
    assert response.status_code == 200
    app.dependency_overrides = {}

def test_save_config_api(mocker, mock_admin_user):
    from telegram_rutor_bot.web.auth import get_current_admin_if_configured
    app.dependency_overrides[get_current_admin_if_configured] = lambda: mock_admin_user
    
    mocker.patch("telegram_rutor_bot.web.config_api.update_db_config", AsyncMock())
    mocker.patch("telegram_rutor_bot.web.config_api._init_users", AsyncMock())
    mocker.patch("telegram_rutor_bot.web.config_api._save_system_searches", AsyncMock())
    mocker.patch("telegram_rutor_bot.web.config_api._update_qbittorrent_prefs", AsyncMock())
    
    mocker.patch("telegram_rutor_bot.web.config_api.settings")
    
    mock_session = AsyncMock()
    mocker.patch("telegram_rutor_bot.web.config_api.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    
    config_data = {
        "telegram": {"token": "t1", "initial_users": []},
        "torrent": {"client": "qbittorrent", "host": "localhost", "port": 8080, "username": "u", "password": "p"},
        "searches": []
    }
    
    response = client.post("/api/config", json=config_data)
    assert response.status_code == 200
    app.dependency_overrides = {}
