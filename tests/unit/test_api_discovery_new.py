import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.api.routes.discovery import get_trending, search_discovery

@pytest.mark.asyncio
async def test_get_trending_api(mocker):
    mocker.patch("telegram_rutor_bot.api.routes.discovery.tmdb.get_trending", AsyncMock(return_value=[{"id": 1, "title": "T"}]))
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)
    res = await get_trending(media_type="movie", time_window="week", user=MagicMock(), db=mock_db)
    assert len(res) == 1

@pytest.mark.asyncio
async def test_search_discovery_api(mocker):
    mocker.patch("telegram_rutor_bot.api.routes.discovery.tmdb.search_multi", AsyncMock(return_value=[{"id": 1, "title": "T", "media_type": "movie"}]))
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)
    res = await search_discovery(q="test", user=MagicMock(), db=mock_db)
    assert len(res) == 1
