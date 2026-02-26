import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.torrent_clients.qbittorrent import QBittorrentClient, TorrentClientError

@pytest.fixture
def qb_client():
    return QBittorrentClient("localhost", 8080, "admin", "admin")

@pytest.mark.asyncio
async def test_qb_connect_flows(mocker, qb_client):
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.__aenter__.return_value = mock_http
    mocker.patch("httpx.AsyncClient", return_value=mock_http)
    
    # Case 1: Version check success (bypassed)
    mock_http.get.return_value = MagicMock(status_code=200)
    await qb_client.connect()
    assert qb_client._authenticated is True
    
    # Case 2: Version check fail, login success
    mock_http.get.side_effect = httpx.HTTPError("Fail")
    mock_http.post.return_value = MagicMock(status_code=200, text="Ok.", cookies={})
    qb_client._authenticated = False
    await qb_client.connect()
    assert qb_client._authenticated is True
    
    # Case 3: Login fail
    mock_http.post.return_value = MagicMock(status_code=401, text="Error")
    qb_client._authenticated = False
    with pytest.raises(TorrentClientError):
        await qb_client.connect()

@pytest.mark.asyncio
async def test_qb_request_retry_auth(mocker, qb_client):
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    mock_http.__aenter__.return_value = mock_http
    mocker.patch("httpx.AsyncClient", return_value=mock_http)
    
    qb_client._client = mock_http
    
    # First call 403, second success
    mock_resp_403 = MagicMock(status_code=403)
    mock_resp_200 = MagicMock(status_code=200, text="Ok")
    mock_resp_200.headers = {}
    mock_http.request.side_effect = [mock_resp_403, mock_resp_200]
    
    # Mock connect to avoid real HTTP
    mocker.patch.object(qb_client, "connect", AsyncMock())
    
    res = await qb_client._request("GET", "test")
    assert res == "Ok"
    assert qb_client.connect.called

@pytest.mark.asyncio
async def test_qb_add_torrent_full(mocker, qb_client):
    mocker.patch.object(qb_client, "_request", AsyncMock(return_value="Ok."))
    # Mock list_torrents to find the added one
    mocker.patch.object(qb_client, "list_torrents", AsyncMock(return_value=[{"magnet_uri": "magnet:?xt=urn:btih:123", "hash": "h1"}]))
    
    res = await qb_client.add_torrent("magnet:?xt=urn:btih:123", category="FILMS", ratio_limit=2.0)
    assert res["hash"] == "h1"

@pytest.mark.asyncio
async def test_qb_other_methods(mocker, qb_client):
    mocker.patch.object(qb_client, "_request", AsyncMock())
    
    # pause
    await qb_client.pause_torrent("h1")
    # resume
    await qb_client.resume_torrent("h1")
    # remove
    await qb_client.remove_torrent("h1", delete_files=True)
    
    # get_torrent
    qb_client._request.return_value = [{"hash": "h1", "name": "T"}]
    res = await qb_client.get_torrent("h1")
    assert res["name"] == "T"
    
    # preferences
    qb_client._request.return_value = {"pref1": "val1"}
    assert await qb_client.get_app_preferences() == {"pref1": "val1"}
    
    await qb_client.set_app_preferences({"p": "v"})
    
    assert True
