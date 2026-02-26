from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.db.models import Film, Torrent
from telegram_rutor_bot.helpers import _clean_torrent_name, _format_film_with_details


@pytest.mark.asyncio
async def test_format_film_with_details_success(mocker):
    mock_session = AsyncMock()
    film = MagicMock(spec=Film)
    film.id = 1
    film.name = 'Matrix'
    film.year = 1999
    film.rating = 8.5
    film.genres = 'Action'
    film.poster_url = 'http://p.jpg'
    film.kp_rating = 8.5

    torrent = MagicMock(spec=Torrent)
    torrent.id = 1
    torrent.name = 'The Matrix (1999) BDRip'
    torrent.size = 1073741824  # 1 GB
    torrent.link = '/t/1'

    mocker.patch('telegram_rutor_bot.helpers.get_torrent_info', AsyncMock(return_value=('info', b'p', [], 'url', {})))

    note = await _format_film_with_details(mock_session, film, [torrent])
    assert note['type'] == 'photo'


def test_clean_torrent_name_variations():
    assert _clean_torrent_name('Matrix (1999) BDRip', 'Matrix', 1999) == 'BDRip'
