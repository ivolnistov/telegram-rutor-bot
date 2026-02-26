from telegram_rutor_bot.rutor.parser import _parse_genre_from_lines, _is_potential_series, _download_image
import pytest
import httpx
from unittest.mock import MagicMock, AsyncMock

def test_parse_genre_from_lines():
    lines = ["Other: something", "Жанр: Боевик, Драма", "Year: 2024"]
    assert _parse_genre_from_lines(lines) == "Боевик, Драма"
    assert _parse_genre_from_lines(["No genre here"]) is None

def test_is_potential_series():
    assert _is_potential_series("FILMS", "драма, криминал") is True
    assert _is_potential_series("FILMS", "комедия") is False
    assert _is_potential_series("TVSHOWS", "драма") is False
    assert _is_potential_series(None, "драма") is False

@pytest.mark.asyncio
async def test_download_image_mock(mocker):
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = b"fake_data"
    mock_client.get.return_value = mock_response
    
    data = await _download_image(mock_client, "/img.jpg")
    assert data == b"fake_data"
    mock_client.get.assert_called_once()
