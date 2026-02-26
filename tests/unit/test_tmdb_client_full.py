import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.clients.tmdb import TmdbClient

@pytest.fixture
def tmdb_client(mocker):
    mocker.patch("telegram_rutor_bot.clients.tmdb.settings.tmdb_api_key", "test_key")
    mocker.patch("telegram_rutor_bot.clients.tmdb.settings.tmdb_session_id", "test_session")
    return TmdbClient()

@pytest.mark.asyncio
async def test_tmdb_get_base_logic(mocker, tmdb_client):
    # Success path
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [{"id": 1}]}
    
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.get.return_value = mock_resp
    mock_http.__aenter__.return_value = mock_http
    
    mocker.patch("httpx.AsyncClient", return_value=mock_http)
    
    res = await tmdb_client._get("/test")
    assert res == {"results": [{"id": 1}]}
    
    # Error path
    mock_http.get.side_effect = httpx.HTTPError("Fail")
    res_err = await tmdb_client._get("/test")
    assert res_err == {}

@pytest.mark.asyncio
async def test_tmdb_auth_methods(mocker, tmdb_client):
    # create_request_token
    tmdb_client._get = AsyncMock(return_value={"request_token": "token123"})
    assert await tmdb_client.create_request_token() == "token123"
    
    # create_session_id success
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.json.return_value = {"session_id": "sess123"}
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.post.return_value = mock_resp
    mock_http.__aenter__.return_value = mock_http
    mocker.patch("httpx.AsyncClient", return_value=mock_http)
    
    assert await tmdb_client.create_session_id("token") == "sess123"
    
    # create_session_id error
    mock_http.post.side_effect = httpx.HTTPError("Fail")
    assert await tmdb_client.create_session_id("token") is None

@pytest.mark.asyncio
async def test_tmdb_search_and_trending(mocker, tmdb_client):
    tmdb_client._get = AsyncMock(return_value={"results": [{"id": 100}]})
    
    # trending
    res = await tmdb_client.get_trending()
    assert len(res) == 1
    
    # search_multi
    assert len(await tmdb_client.search_multi("query")) == 1
    assert await tmdb_client.search_multi("") == []
    
    # search_movie
    assert len(await tmdb_client.search_movie("matrix", year=1999)) == 1
    
    # search_tv
    assert len(await tmdb_client.search_tv("show", year=2024)) == 1

@pytest.mark.asyncio
async def test_tmdb_details_and_recs(mocker, tmdb_client):
    tmdb_client._get = AsyncMock(return_value={"id": 1})
    
    # get_details
    assert await tmdb_client.get_details("movie", 1, append_to_response="credits") == {"id": 1}
    
    # get_recommendations
    tmdb_client._get.return_value = {"results": [{"id": 2}]}
    assert len(await tmdb_client.get_recommendations("movie", 1)) == 1
    
    # get_account_states
    tmdb_client._get.return_value = {"rated": True}
    assert await tmdb_client.get_account_states("movie", 1) == {"rated": True}

@pytest.mark.asyncio
async def test_tmdb_rating_ops(mocker, tmdb_client):
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.__aenter__.return_value = mock_http
    mocker.patch("httpx.AsyncClient", return_value=mock_http)
    
    # rate_media success
    mock_http.post.return_value = MagicMock(status_code=200)
    assert await tmdb_client.rate_media("movie", 1, 8.5) is True
    
    # rate_media fail
    mock_http.post.side_effect = httpx.HTTPError("Fail")
    assert await tmdb_client.rate_media("movie", 1, 8.5) is False
    
    # delete_rating success
    mock_http.delete.return_value = MagicMock(status_code=200)
    mock_http.delete.side_effect = None
    assert await tmdb_client.delete_rating("movie", 1) is True
    
    # delete_rating fail
    mock_http.delete.side_effect = httpx.HTTPError("Fail")
    assert await tmdb_client.delete_rating("movie", 1) is False

@pytest.mark.asyncio
async def test_tmdb_account_and_lists(mocker, tmdb_client):
    tmdb_client.get_account_info = AsyncMock(return_value={"id": 500})
    tmdb_client._get = AsyncMock(return_value={"results": [{"id": 1}]})
    
    # get_rated_media
    assert len(await tmdb_client.get_rated_media("movie")) == 1
    assert len(await tmdb_client.get_rated_media("tv")) == 1
    
    # get_watchlist
    assert len(await tmdb_client.get_watchlist("movie")) == 1
    
    # add_to_watchlist success
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.__aenter__.return_value = mock_http
    mock_http.post.return_value = MagicMock(status_code=201)
    mocker.patch("httpx.AsyncClient", return_value=mock_http)
    
    assert await tmdb_client.add_to_watchlist("movie", 1) is True
    
    # add_to_watchlist fail
    mock_http.post.side_effect = httpx.HTTPError("Fail")
    assert await tmdb_client.add_to_watchlist("movie", 1) is False

@pytest.mark.asyncio
async def test_tmdb_personal_recs(mocker, tmdb_client):
    # With rated media
    tmdb_client.get_rated_media = AsyncMock(return_value=[{"id": 10}])
    tmdb_client.get_recommendations = AsyncMock(return_value=[{"id": 11}])
    
    res = await tmdb_client.get_personal_recommendations()
    assert res == [{"id": 11}]
    
    # Without rated media (fallback)
    tmdb_client.get_rated_media.return_value = []
    tmdb_client.get_trending = AsyncMock(return_value=[{"id": 12}])
    
    res_fallback = await tmdb_client.get_personal_recommendations()
    assert res_fallback == [{"id": 12}]
