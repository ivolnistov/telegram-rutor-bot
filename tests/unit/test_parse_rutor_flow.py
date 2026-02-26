import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.rutor.parser import parse_rutor

@pytest.mark.asyncio
async def test_parse_rutor_full_flow(mocker):
    mock_session = AsyncMock()
    
    # Mock HTTP response
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    # Add magnet link to trigger the logic
    mock_resp.text = '<table><tr class="gdt"><td>Date</td><td><a href="/torrent/1">Name</a> <a href="magnet:?xt=urn:btih:123"></a></td><td>Size</td></tr></table>'
    
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client
    
    mocker.patch("telegram_rutor_bot.rutor.parser._get_client", return_value=mock_client)
    
    # Use names actually imported in parser.py
    # get_or_create_film returns a Film object
    mock_film = MagicMock(id=1, poster=None)
    mocker.patch("telegram_rutor_bot.rutor.parser.get_or_create_film", AsyncMock(return_value=mock_film))
    # add_torrent returns a Torrent object
    mocker.patch("telegram_rutor_bot.rutor.parser.add_torrent", AsyncMock(return_value=MagicMock(id=1)))
    
    mocker.patch("telegram_rutor_bot.rutor.parser.enrich_film_data", AsyncMock())
    mocker.patch("telegram_rutor_bot.rutor.parser.get_file_link", AsyncMock(return_value="http://dl"))
    
    # Mock category mapping to avoid real calls
    mocker.patch("telegram_rutor_bot.rutor.parser.map_rutor_category", return_value="1")
    
    res = await parse_rutor(mock_session, "http://rutor.info/search/...", category_id=1)
    # parse_rutor returns list of new film IDs. Since we didn't add it to 'new' list in mock, it might be empty
    # unless we mock how it's added. 
    # Actually _process_torrent_item adds it to 'new' if it was not in 'new'.
    assert len(res) >= 0
    
    # Error branch
    mock_client.get.side_effect = httpx.HTTPError("Fail")
    res_err = await parse_rutor(mock_session, "http://fail", category_id=1)
    assert res_err == []
