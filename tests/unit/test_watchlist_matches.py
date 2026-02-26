from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.services.watchlist import _download_best_torrent_for_film, _find_relevant_torrents


def test_find_relevant_torrents():
    film = MagicMock()
    film.name = 'The Matrix'
    film.original_title = 'The Matrix'

    torrents = [MagicMock(name='Matrix'), MagicMock(name='Avatar')]
    torrents[0].name = 'The Matrix (1999) 1080p'
    torrents[1].name = 'Avatar 2'

    relevant = _find_relevant_torrents(film, torrents)
    assert len(relevant) == 1
    assert 'Matrix' in relevant[0].name


@pytest.mark.asyncio
async def test_download_best_torrent_for_film_no_match(mocker):
    session = AsyncMock()
    film = MagicMock()
    torrents = []

    # Should just return
    await _download_best_torrent_for_film(session, film, torrents)
    session.commit.assert_not_called()
