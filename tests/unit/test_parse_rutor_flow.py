import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.rutor.parser import parse_rutor

@pytest.mark.asyncio
async def test_parse_flow_v3(mocker):
    mock_session = AsyncMock()
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.text = '<table><tr class="gdt"><td>Date</td><td><a href="/torrent/1">N</a> <a href="magnet:?xt=urn:btih:1"></a></td><td>S</td></tr></table>'
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client
    mocker.patch("telegram_rutor_bot.rutor.parser._get_client", return_value=mock_client)
    
    mocker.patch("telegram_rutor_bot.rutor.parser.get_or_create_film", AsyncMock(return_value=MagicMock(id=1, poster=None)))
    mocker.patch("telegram_rutor_bot.rutor.parser.add_torrent", AsyncMock(return_value=MagicMock(id=1)))
    mocker.patch("telegram_rutor_bot.rutor.parser.enrich_film_data", AsyncMock())
    mocker.patch("telegram_rutor_bot.rutor.parser.get_file_link", AsyncMock(return_value="l"))
    mocker.patch("telegram_rutor_bot.rutor.parser.map_rutor_category", return_value="1")
    
    res = await parse_rutor(mock_session, "http://t", category_id=1)
    assert isinstance(res, list)
