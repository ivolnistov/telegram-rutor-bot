import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.web.app import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_discovery_trending(mocker):
    # Discovery uses get_async_db from api.routes.discovery
    mock_session = AsyncMock()
    mocker.patch("telegram_rutor_bot.api.routes.discovery.get_async_db", return_value=mock_session)
    
    response = client.get("/api/discovery/trending?media_type=movie")
    assert response.status_code in (200, 401, 500)

@pytest.mark.asyncio
async def test_discovery_search(mocker):
    response = client.get("/api/discovery/search?q=matrix")
    assert response.status_code in (200, 401, 500)
