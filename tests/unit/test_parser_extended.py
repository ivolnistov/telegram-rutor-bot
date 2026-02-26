from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from bs4 import BeautifulSoup

from telegram_rutor_bot.rutor.parser import _extract_details_from_table, _parse_torrent_page_details, get_torrent_info


@pytest.mark.asyncio
async def test_get_torrent_info_error(mocker):
    # Mock httpx failure
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPError('Network error')
    mocker.patch(
        'httpx.AsyncClient',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_client), __aexit__=AsyncMock()),
    )
    pass


def test_extract_details_from_table_empty():
    soup = BeautifulSoup('<table></table>', 'html.parser')
    res = _extract_details_from_table(soup)
    assert res == {}


def test_parse_torrent_page_details_internal():
    html = """
    <html><body>
    <div id="details">
        <table>
            <tr><td><b>IMDB:</b></td><td><a href="https://www.imdb.com/title/tt1234567/">Link</a></td></tr>
        </table>
        <pre>Description content</pre>
    </div>
    </body></html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    imdb_url, kp_url, metadata = _parse_torrent_page_details(soup)
    assert 'tt123' in imdb_url
    assert metadata['imdb_url'] == imdb_url


@pytest.mark.asyncio
async def test_get_torrent_info_success(mocker):
    html = "<html><body><div id='details'>...</div></body></html>"
    mock_response = MagicMock()
    mock_response.text = html
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mocker.patch(
        'httpx.AsyncClient',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_client), __aexit__=AsyncMock()),
    )

    mocker.patch('telegram_rutor_bot.rutor.parser._extract_images', AsyncMock(return_value=(None, None, [])))

    res = await get_torrent_info('/test')
    assert len(res) == 5


@pytest.mark.asyncio
async def test_fetch_rutor_torrents_success(mocker):
    html = "<html><body><div id='index'>...</div></body></html>"
    mock_response = MagicMock()
    mock_response.text = html
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mocker.patch(
        'httpx.AsyncClient',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_client), __aexit__=AsyncMock()),
    )

    mocker.patch(
        'telegram_rutor_bot.rutor.parser.localize', return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock())
    )

    from telegram_rutor_bot.rutor.parser import fetch_rutor_torrents

    res = await fetch_rutor_torrents('http://rutor.info/test')
    assert isinstance(res, list)


@pytest.mark.asyncio
async def test_download_torrent_success(mocker):
    from telegram_rutor_bot.db.models import Film, Torrent

    mock_film = MagicMock(spec=Film)
    mock_film.category_rel = None

    mock_torrent = MagicMock(spec=Torrent)
    mock_torrent.link = '/t/1'
    mock_torrent.name = 'Film Name'
    mock_torrent.magnet = 'mag1'
    mock_torrent.film = mock_film

    mock_response = MagicMock()
    mock_response.text = '<html>...</html>'
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mocker.patch(
        'telegram_rutor_bot.rutor.parser._get_client',
        return_value=mocker.MagicMock(__aenter__=AsyncMock(return_value=mock_client), __aexit__=AsyncMock()),
    )

    mocker.patch('telegram_rutor_bot.rutor.parser._extract_genre_from_details', return_value=('Action', 'Фильмы'))

    mock_tc = AsyncMock()
    # Fixed return value
    mock_tc.add_torrent.return_value = {'status': 'ok'}
    mocker.patch('telegram_rutor_bot.rutor.parser.get_torrent_client', return_value=mock_tc)

    from telegram_rutor_bot.rutor.parser import download_torrent

    res = await download_torrent(mock_torrent)

    assert res['status'] == 'ok'
