import pytest
from fastapi.testclient import TestClient
from fastapi.responses import HTMLResponse
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.web.app import app
from telegram_rutor_bot.db.models import User

client = TestClient(app)

@pytest.fixture
def mock_admin():
    u = User(id=1, chat_id=123, username="admin", is_admin=True, is_authorized=True)
    return u

@pytest.fixture(autouse=True)
def bypass_auth(mocker, mock_admin):
    from telegram_rutor_bot.web.auth import get_current_admin_user, get_current_user
    app.dependency_overrides[get_current_admin_user] = lambda: mock_admin
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    yield
    app.dependency_overrides = {}

def test_app_health(mocker):
    mocker.patch("telegram_rutor_bot.web.app.init_db")
    mocker.patch("telegram_rutor_bot.web.app.broker.startup", AsyncMock())
    res = client.get("/api/health")
    assert res.status_code == 200

def test_app_searches(mocker):
    mocker.patch("telegram_rutor_bot.web.app.get_searches", AsyncMock(return_value=[]))
    assert client.get("/api/searches").status_code == 200

def test_app_films_update(mocker):
    # Mock endpoint to return dict directly
    mocker.patch("telegram_rutor_bot.web.app.update_film", AsyncMock(return_value={"status": "ok"}))
    res = client.put("/api/films/1", data={"user_rating": 5})
    assert res.status_code == 200

def test_app_user_status(mocker):
    mocker.patch("telegram_rutor_bot.web.app.update_user_status", AsyncMock(return_value={"status": "ok"}))
    res = client.patch("/api/users/1/status", data={"is_authorized": "true"})
    assert res.status_code == 200

def test_app_downloads(mocker):
    mock_tc = AsyncMock()
    mock_tc.list_torrents.return_value = []
    mocker.patch("telegram_rutor_bot.web.app.get_torrent_client", return_value=mock_tc)
    mocker.patch("telegram_rutor_bot.web.app._execute_torrent_action", AsyncMock(return_value={"status": "ok"}))
    
    assert client.get("/api/downloads").status_code == 200
    assert client.post("/api/downloads/hash/pause").status_code == 200
