from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.db.models import Film
from telegram_rutor_bot.services.matcher import TmdbMatcher


@pytest.mark.asyncio
async def test_match_films_success(mocker):
    mock_session = AsyncMock()

    # Mock get_unlinked_films. `name=` is reserved by MagicMock — set it after construction.
    mock_film = MagicMock(spec=Film, id=1, year=1999, ru_name=None, original_title=None)
    mock_film.name = 'The Matrix'
    mocker.patch('telegram_rutor_bot.services.matcher.get_unlinked_films', AsyncMock(return_value=[mock_film]))
    mocker.patch('telegram_rutor_bot.services.matcher.update_film_metadata', AsyncMock(return_value=True))

    matcher = TmdbMatcher(mock_session)
    matcher.tmdb = MagicMock()
    matcher.tmdb.search_movie = AsyncMock(
        return_value=[
            {
                'id': 603,
                'title': 'The Matrix',
                'original_title': 'The Matrix',
                'release_date': '1999-03-31',
                'vote_average': 8.7,
                'poster_path': '/path.jpg',
            }
        ]
    )

    count = await matcher.match_films()
    assert count == 1
    assert matcher.tmdb.search_movie.called


@pytest.mark.asyncio
async def test_match_films_no_match(mocker):
    mock_session = AsyncMock()
    mock_film = MagicMock(spec=Film, id=2, year=2020, ru_name=None, original_title=None)
    mock_film.name = 'Unknown Film'
    mocker.patch('telegram_rutor_bot.services.matcher.get_unlinked_films', AsyncMock(return_value=[mock_film]))

    matcher = TmdbMatcher(mock_session)
    matcher.tmdb = MagicMock()
    matcher.tmdb.search_movie = AsyncMock(return_value=[])

    count = await matcher.match_films()
    assert count == 0


def test_best_match_rejects_year_mismatch():
    """Real bug: TMDB's `year` filter is loose. Searching `Утес` 2026 returned
    `Рыбка Поньо на утёсе` (2008) as the only result. Matcher must reject it."""
    ponyo_2008 = {
        'id': 12429,
        'title': 'Рыбка Поньо на утёсе',
        'original_title': '崖の上のポニョ',
        'release_date': '2008-07-19',
    }
    assert TmdbMatcher._best_match([ponyo_2008], 'Утес', 2026) is None


def test_best_match_accepts_single_year_match_with_low_similarity():
    """When TMDB returns a single result whose year matches the query,
    accept it even if title similarity is weak (handles transliteration drift)."""
    bluff_2026 = {
        'id': 799882,
        'title': 'Утёс',
        'original_title': 'The Bluff',
        'release_date': '2026-02-17',
    }
    match = TmdbMatcher._best_match([bluff_2026], 'Блеф', 2026)
    assert match is not None
    assert match['id'] == 799882


def test_best_match_picks_high_similarity_over_low():
    """When multiple year-matched results exist, pick the one whose title
    most closely resembles the query."""
    candidates = [
        {'id': 1, 'title': 'Wrong Movie', 'original_title': 'Wrong Movie', 'release_date': '2024-01-01'},
        {'id': 2, 'title': 'Canary Black', 'original_title': 'Canary Black', 'release_date': '2024-10-10'},
    ]
    match = TmdbMatcher._best_match(candidates, 'Canary Black', 2024)
    assert match is not None
    assert match['id'] == 2


def test_best_match_handles_tv_results():
    """For TV-show searches the result has `first_air_date` instead of `release_date`."""
    wwk = {
        'id': 87428,
        'name': 'Why Women Kill',
        'original_name': 'Why Women Kill',
        'first_air_date': '2019-08-15',
    }
    match = TmdbMatcher._best_match([wwk], 'Why Women Kill', 2019)
    assert match is not None
    assert match['id'] == 87428
