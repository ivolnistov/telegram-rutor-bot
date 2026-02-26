import pytest
import httpx
from bs4 import BeautifulSoup
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.rutor.parser import get_torrent_details

@pytest.mark.asyncio
async def test_get_torrent_details_full(mocker):
    mock_session = AsyncMock()
    
    # Mock torrent
    mock_torrent = MagicMock(id=1, link="/torrent/1")
    mocker.patch("telegram_rutor_bot.rutor.parser.get_torrent_by_id", AsyncMock(return_value=mock_torrent))
    
    # Mock HTTP response
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.text = '''
    <div id="details">
        <table>
            <tr><td>Описание</td><td>Great movie</td></tr>
            <tr><td>Видео</td><td>1080p</td></tr>
            <tr><td>Качество</td><td>BDRip</td></tr>
            <tr><td>Перевод</td><td>Dub</td></tr>
            <tr><td>Субтитры</td><td>None</td></tr>
        </table>
    </div>
    <a href="http://www.imdb.com/title/tt123">IMDB</a>
    '''
    
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client
    
    mocker.patch("telegram_rutor_bot.rutor.parser._get_client", return_value=mock_client)
    
    res = await get_torrent_details(mock_session, 1)
    assert res["description"] == "Great movie"
    assert res["video_quality"] == "1080p"
    assert res["quality"] == "BDRip"
    assert res["translate_quality"] == "Dub"
    assert res["subtitles"] == "None"
    assert res["url"] == "http://www.imdb.com/title/tt123"
    
    # Torrent not found
    mocker.patch("telegram_rutor_bot.rutor.parser.get_torrent_by_id", AsyncMock(return_value=None))
    assert await get_torrent_details(mock_session, 1) == {}
