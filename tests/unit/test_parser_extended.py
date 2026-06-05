from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from bs4 import BeautifulSoup

from telegram_rutor_bot.db.models import Film, Torrent
from telegram_rutor_bot.rutor.parser import (
    _extract_details_from_table,
    _get_category_folder,
    _normalize_category_folder,
    _parse_torrent_page_details,
    _resolve_download_dir,
    add_torrent_from_page_url,
    download_torrent,
    fetch_rutor_torrents,
    get_torrent_info,
)


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
    imdb_url, _, metadata = _parse_torrent_page_details(soup)
    assert 'tt123' in imdb_url
    assert metadata['imdb_url'] == imdb_url


def test_normalize_category_folder_uses_qbittorrent_download_root():
    assert _normalize_category_folder('CARTOONS') == '/downloads/CARTOONS'
    assert _normalize_category_folder('/downloads/CARTOONS') == '/downloads/CARTOONS'


@pytest.mark.asyncio
async def test_get_category_folder_matches_folder_case_insensitively(mocker):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 'CARTOONS'

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mocker.patch(
        'telegram_rutor_bot.rutor.parser.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()),
    )

    assert await _get_category_folder('CARTOONS') == '/downloads/CARTOONS'


@pytest.mark.asyncio
async def test_resolve_download_dir_normalizes_film_category_folder():
    mock_category = MagicMock()
    mock_category.folder = 'FILMS'

    mock_film = MagicMock(spec=Film)
    mock_film.category_rel = mock_category

    mock_torrent = MagicMock(spec=Torrent)
    mock_torrent.film = mock_film

    assert await _resolve_download_dir(mock_torrent, 'CARTOONS') == '/downloads/FILMS'


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

    res = await fetch_rutor_torrents('http://rutor.info/test')
    assert isinstance(res, list)


@pytest.mark.asyncio
async def test_download_torrent_success(mocker):
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
    mocker.patch('telegram_rutor_bot.rutor.parser._get_category_folder', AsyncMock(return_value=None))

    mock_tc = AsyncMock()
    # Fixed return value
    mock_tc.add_torrent.return_value = {'status': 'ok'}
    mocker.patch('telegram_rutor_bot.rutor.parser.get_torrent_client', return_value=mock_tc)

    res = await download_torrent(mock_torrent)

    assert res['status'] == 'ok'


@pytest.mark.asyncio
async def test_download_torrent_uses_detected_category_folder(mocker):
    mock_film = MagicMock(spec=Film)
    mock_film.category_rel = None
    mock_film.tmdb_id = None

    mock_torrent = MagicMock(spec=Torrent)
    mock_torrent.link = '/t/1'
    mock_torrent.name = 'Cartoon Name'
    mock_torrent.magnet = 'magnet:?xt=urn:btih:cartoon'
    mock_torrent.film = mock_film

    mock_response = MagicMock()
    mock_response.text = '<html></html>'
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mocker.patch(
        'telegram_rutor_bot.rutor.parser._get_client',
        return_value=mocker.MagicMock(__aenter__=AsyncMock(return_value=mock_client), __aexit__=AsyncMock()),
    )
    mocker.patch('telegram_rutor_bot.rutor.parser._extract_genre_from_details', return_value=('animation', None))
    mocker.patch('telegram_rutor_bot.rutor.parser._get_category_folder', AsyncMock(return_value='/downloads/cartoons'))

    mock_tc = AsyncMock()
    mock_tc.add_torrent.return_value = {'status': 'ok'}
    mocker.patch('telegram_rutor_bot.rutor.parser.get_torrent_client', return_value=mock_tc)

    await download_torrent(mock_torrent)

    mock_tc.add_torrent.assert_awaited_once_with(
        'magnet:?xt=urn:btih:cartoon',
        download_dir='/downloads/cartoons',
        category='CARTOONS',
        rename='Cartoon Name',
        tags=None,
    )


@pytest.mark.asyncio
async def test_add_torrent_from_page_url_uses_detected_category_folder(mocker):
    mock_response = MagicMock()
    mock_response.text = '<html><h1>Cartoon Name (2024)</h1><a href="magnet:?xt=urn:btih:cartoon">m</a></html>'
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mocker.patch(
        'telegram_rutor_bot.rutor.parser._get_client',
        return_value=mocker.MagicMock(__aenter__=AsyncMock(return_value=mock_client), __aexit__=AsyncMock()),
    )
    mocker.patch('telegram_rutor_bot.rutor.parser._extract_genre_from_details', return_value=('animation', None))
    mocker.patch('telegram_rutor_bot.rutor.parser._get_category_folder', AsyncMock(return_value='/downloads/cartoons'))

    mock_tc = AsyncMock()
    mocker.patch('telegram_rutor_bot.rutor.parser.get_torrent_client', return_value=mock_tc)

    result = await add_torrent_from_page_url('/torrent/1/cartoon')

    assert result['category'] == 'CARTOONS'
    mock_tc.add_torrent.assert_awaited_once_with(
        'magnet:?xt=urn:btih:cartoon',
        download_dir='/downloads/cartoons',
        category='CARTOONS',
        rename='Cartoon Name',
    )
