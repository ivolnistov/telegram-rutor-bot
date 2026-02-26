import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.web.app import app

client = TestClient(app)

@pytest.fixture
def mock_admin():
    u = MagicMock()
    u.is_admin = True
    u.is_authorized = True
    return u

def test_config_api_full_save(mocker, mock_admin):
    from telegram_rutor_bot.web.auth import get_current_admin_if_configured
    app.dependency_overrides[get_current_admin_if_configured] = lambda: mock_admin
    
    mocker.patch("telegram_rutor_bot.web.config_api.update_db_config", AsyncMock())
    mocker.patch("telegram_rutor_bot.web.config_api._init_users", AsyncMock())
    mocker.patch("telegram_rutor_bot.web.config_api._save_system_searches", AsyncMock())
    mocker.patch("telegram_rutor_bot.web.config_api._update_qbittorrent_prefs", AsyncMock())
    mocker.patch("telegram_rutor_bot.web.config_api.get_async_session")
    mocker.patch("telegram_rutor_bot.web.config_api.settings")
    
    config_data = {
        "telegram": {"token": "t", "initial_users": []},
        "torrent": {"client": "qbittorrent", "host": "h", "port": 80, "username": "u", "password": "p"},
        "searches": []
    }
    
    response = client.post("/api/config", json=config_data)
    assert response.status_code == 200
    app.dependency_overrides = {}
