import pytest
from fastapi.testclient import TestClient
from fastapi.responses import HTMLResponse
from unittest.mock import AsyncMock, MagicMock, patch
from telegram_rutor_bot.web.app import app
from telegram_rutor_bot.db.models import User, Search, Film, Torrent, Category, TaskExecution
from telegram_rutor_bot.schemas import StatusResponse, UserResponse, CategoryResponse

client = TestClient(app)

@pytest.fixture
def mock_admin_dict():
    return {
        "id": 1,
        "chat_id": 123,
        "username": "admin",
        "name": "Admin",
        "is_authorized": True,
        "is_admin": True,
        "is_tfa_enabled": False,
        "language": "en",
        "password": None
    }

@pytest.fixture
def bypass_auth(mocker, mock_admin_dict):
    from telegram_rutor_bot.web.auth import get_current_admin_user, get_current_user
    admin_user = User(**mock_admin_dict)
    app.dependency_overrides[get_current_admin_user] = lambda: admin_user
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    mock_session = AsyncMock()
    mocker.patch("telegram_rutor_bot.web.app.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    
    yield mock_session
    app.dependency_overrides = {}

def test_health_check_full(mocker):
    mocker.patch("telegram_rutor_bot.web.app.get_async_session")
    mocker.patch("telegram_rutor_bot.web.app.broker.startup", AsyncMock())
    mocker.patch("telegram_rutor_bot.web.app.get_torrent_client", return_value=AsyncMock())
    
    response = client.get("/api/health")
    assert response.status_code == 200

def test_searches_endpoints(mocker, bypass_auth):
    mocker.patch("telegram_rutor_bot.web.app.get_searches", AsyncMock(return_value=[]))
    assert client.get("/api/searches").status_code == 200
    
    mocker.patch("telegram_rutor_bot.web.app.get_or_create_user_by_chat_id", AsyncMock(return_value=MagicMock(id=1)))
    mocker.patch("telegram_rutor_bot.web.app.add_search_to_db", AsyncMock(return_value=1))
    mocker.patch("telegram_rutor_bot.web.app.subscribe", AsyncMock(return_value=(True, "")))
    res = client.post("/api/searches", data={"url": "http://t", "cron": "* * * * *", "chat_id": "123"})
    assert res.status_code == 200

def test_torrents_and_films_endpoints(mocker, bypass_auth):
    mocker.patch("telegram_rutor_bot.web.app.get_recent_torrents", AsyncMock(return_value=[]))
    assert client.get("/api/torrents").status_code == 200
    
    mocker.patch("telegram_rutor_bot.web.app.get_films", AsyncMock(return_value=[]))
    assert client.get("/api/films").status_code == 200
    
    # Return dict instead of object to satisfy FastAPI validation if it's being picky
    mocker.patch("telegram_rutor_bot.web.app.update_film", AsyncMock(return_value={"status": "ok"}))
    assert client.put("/api/films/1", data={"user_rating": 5}).status_code == 200

def test_users_and_categories_endpoints(mocker, bypass_auth, mock_admin_dict):
    mocker.patch("telegram_rutor_bot.web.app.get_all_users", AsyncMock(return_value=[]))
    assert client.get("/api/users").status_code == 200
    
    mocker.patch("telegram_rutor_bot.web.app.update_user_status", AsyncMock(return_value={"status": "ok"}))
    assert client.patch("/api/users/1/status", data={"is_admin": "true"}).status_code == 200
    
    mocker.patch("telegram_rutor_bot.web.app.get_categories", AsyncMock(return_value=[]))
    assert client.get("/api/categories").status_code == 200
    
    mocker.patch("telegram_rutor_bot.web.app.update_category_api", AsyncMock(return_value={"status": "ok"}))
    assert client.patch("/api/categories/1", data={"name": "New"}).status_code == 200

def test_downloads_management(mocker, bypass_auth):
    mock_tc = AsyncMock()
    mocker.patch("telegram_rutor_bot.web.app.get_torrent_client", return_value=mock_tc)
    
    mock_tc.list_torrents.return_value = []
    assert client.get("/api/downloads").status_code == 200
    
    mocker.patch("telegram_rutor_bot.web.app._execute_torrent_action", AsyncMock(return_value={"status": "ok"}))
    
    assert client.post("/api/downloads/hash/pause").status_code == 200
    assert client.post("/api/downloads/hash/resume").status_code == 200
    assert client.delete("/api/downloads/hash").status_code == 200

def test_tasks_endpoint(mocker, bypass_auth):
    mock_session = bypass_auth
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    
    assert client.get("/api/tasks").status_code == 200

def test_serve_spa_scenarios(mocker):
    mocker.patch("telegram_rutor_bot.web.app.settings.is_configured", True)
    mocker.patch("telegram_rutor_bot.web.app.Path.exists", return_value=True)
    mocker.patch("telegram_rutor_bot.web.app.FileResponse", return_value=HTMLResponse("Index"))
    assert client.get("/some/path").status_code == 200
    
    mocker.patch("telegram_rutor_bot.web.app.settings.is_configured", False)
    mocker.patch("telegram_rutor_bot.web.app._serve_wizard", return_value=HTMLResponse("Wizard"))
    assert client.get("/").status_code == 200
