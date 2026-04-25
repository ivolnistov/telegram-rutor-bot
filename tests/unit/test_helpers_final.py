from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.db.models import Film, Torrent
from telegram_rutor_bot.helpers import _clean_torrent_name, _format_film_card


@pytest.mark.asyncio
async def test_format_film_card_returns_poster_and_torrents(mocker):
    mock_session = AsyncMock()
    film = MagicMock(spec=Film)
    film.id = 1
    film.tmdb_id = None  # short-circuits _fetch_tmdb_details to {}
    film.tmdb_media_type = None
    film.name = 'Matrix'
    film.ru_name = None
    film.original_title = None
    film.year = 1999
    film.country = None
    film.poster = 'http://p.jpg'  # already set → skip rutor poster enrichment
    film.rating = '8.5'
    film.kp_rating = None
    film.genres = None

    torrent = MagicMock(spec=Torrent)
    torrent.id = 1
    torrent.name = 'The Matrix (1999) BDRip'
    torrent.sz = 1073741824
    torrent.size = 1073741824  # property on the real model — set directly on the mock
    torrent.seeds = 10
    torrent.link = '/t/1'
    torrent.season = None
    torrent.episode = None

    mocker.patch('telegram_rutor_bot.helpers.get_torrent_info', AsyncMock(return_value=('info', None, [], None, {})))

    notes = await _format_film_card(mock_session, film, [torrent])
    assert len(notes) == 2
    assert notes[0]['type'] == 'photo'
    assert notes[1]['type'] == 'text'


def test_clean_torrent_name_variations():
    assert _clean_torrent_name('Matrix (1999) BDRip', 'Matrix', 1999) == 'BDRip'
