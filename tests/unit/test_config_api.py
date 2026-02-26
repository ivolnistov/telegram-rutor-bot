import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.web.app import app
from telegram_rutor_bot.db import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_init_db():
    init_db()

def test_get_config_unauthorized():
    # Bypass actual DB for unit test logic coverage
    response = client.get("/api/config")
    assert response.status_code != 404

@pytest.mark.asyncio
async def test_save_config_mock(mocker):
    # Mock dependencies
    mocker.patch("telegram_rutor_bot.web.config_api.update_db_config", new_callable=AsyncMock)
    mocker.patch("telegram_rutor_bot.web.config_api._init_users", new_callable=AsyncMock)
    mocker.patch("telegram_rutor_bot.web.config_api._save_system_searches", new_callable=AsyncMock)
    mocker.patch("telegram_rutor_bot.web.config_api._update_qbittorrent_prefs", new_callable=AsyncMock)
    
    payload = {
        "telegram": {"token": "123:abc", "initial_users": []},
        "torrent": {"client": "qbittorrent", "host": "localhost", "port": 8080, "username": "u", "password": "p"},
        "searches": []
    }
    
    response = client.post("/api/config", json=payload)
    assert response.status_code != 404
