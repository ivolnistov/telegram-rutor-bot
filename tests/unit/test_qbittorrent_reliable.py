import pytest
import httpx
import asyncio
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.torrent_clients.qbittorrent import QBittorrentClient

@pytest.mark.asyncio
async def test_qbittorrent_reliable(mocker):
    client = QBittorrentClient("host", 8080, "user", "pass")
    
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.text = "Ok."
    mock_resp.headers = MagicMock()
    mock_resp.headers.get.return_value = "application/json"
    mock_resp.json.return_value = [{"hash": "h1", "name": "T1", "state": "downloading", "size": 100, "progress": 0.5, "magnet_uri": "mag"}]
    
    # Use a real AsyncMock for the client
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_resp
    mock_client.get.return_value = mock_resp
    mock_client.request.return_value = mock_resp
    
    # Mock AsyncClient constructor to return our mock_client
    # And mock_client itself should behave as a context manager
    mock_client.__aenter__.return_value = mock_client
    mocker.patch("httpx.AsyncClient", return_value=mock_client)
    mocker.patch("asyncio.sleep", AsyncMock())
    
    await client.connect()
    assert await client.list_torrents() is not None
    res = await client.add_torrent("mag", "/dir")
    assert isinstance(res, dict)
    await client.disconnect()
