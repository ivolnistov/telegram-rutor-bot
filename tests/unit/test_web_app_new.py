import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.web.app import app

client = TestClient(app)

def test_app_get_endpoints(mocker):
    from telegram_rutor_bot.web.auth import get_current_admin_user
    app.dependency_overrides[get_current_admin_user] = lambda: MagicMock(is_admin=True)
    
    mocker.patch("telegram_rutor_bot.web.app.get_async_session")
    mocker.patch("telegram_rutor_bot.web.app.get_searches", AsyncMock(return_value=[]))
    mocker.patch("telegram_rutor_bot.web.app.get_all_users", AsyncMock(return_value=[]))
    mocker.patch("telegram_rutor_bot.web.app.get_categories", AsyncMock(return_value=[]))
    mocker.patch("telegram_rutor_bot.web.app.get_recent_torrents", AsyncMock(return_value=[]))
    mocker.patch("telegram_rutor_bot.web.app.get_films", AsyncMock(return_value=[]))
    
    # GET /api/searches
    response = client.get("/api/searches")
    assert response.status_code == 200
    
    # GET /api/users
    response = client.get("/api/users")
    assert response.status_code == 200
    
    # GET /api/categories
    response = client.get("/api/categories")
    assert response.status_code == 200
    
    app.dependency_overrides = {}
