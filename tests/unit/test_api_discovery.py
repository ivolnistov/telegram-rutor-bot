import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from telegram_rutor_bot.api.routes.discovery import (
    get_trending, 
    search_discovery, 
    search_on_rutor,
    get_media_details,
    get_recommendations
)

@pytest.mark.asyncio
async def test_get_trending(mocker):
    mock_tmdb = mocker.patch("telegram_rutor_bot.api.routes.discovery.tmdb")
    mock_tmdb.get_trending = AsyncMock(return_value=[{"id": 1, "title": "Trending Film"}])
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)
    user = MagicMock()
    res = await get_trending(media_type="movie", time_window="week", user=user, db=mock_db)
    assert len(res) == 1

@pytest.mark.asyncio
async def test_search_discovery(mocker):
    mock_tmdb = mocker.patch("telegram_rutor_bot.api.routes.discovery.tmdb")
    mock_tmdb.search_multi = AsyncMock(return_value=[{"id": 1, "title": "Searched Film", "media_type": "movie"}])
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)
    user = MagicMock()
    res = await search_discovery(q="test", user=user, db=mock_db)
    assert len(res) == 1

@pytest.mark.asyncio
async def test_get_media_details_api(mocker):
    mock_tmdb = mocker.patch("telegram_rutor_bot.api.routes.discovery.tmdb")
    mock_tmdb.get_details = AsyncMock(return_value={"id": 1, "title": "Movie Details"})
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)
    user = MagicMock()
    res = await get_media_details(media_type="movie", media_id=1, user=user, db=mock_db)
    assert res["title"] == "Movie Details"

@pytest.mark.asyncio
async def test_search_on_rutor_not_movie(mocker):
    user = MagicMock()
    with pytest.raises(HTTPException) as e:
        await search_on_rutor(media_type="tv", media_id=1, user=user, db=AsyncMock())
    assert e.value.status_code == 400

@pytest.mark.asyncio
async def test_search_on_rutor_success(mocker):
    # Mock TMDB
    mocker.patch("telegram_rutor_bot.api.routes.discovery.tmdb.get_details", AsyncMock(return_value={"title": "T"}))
    mocker.patch("telegram_rutor_bot.api.routes.discovery.search_film_on_rutor.kiq", AsyncMock())
    
    mock_db = AsyncMock()
    mock_film = MagicMock()
    mock_film.id = 1
    mock_film.name = "T"
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_film
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    user = MagicMock(chat_id=123)
    res = await search_on_rutor(media_type="movie", media_id=1, user=user, db=mock_db)
    assert res["status"] == "search_started"
