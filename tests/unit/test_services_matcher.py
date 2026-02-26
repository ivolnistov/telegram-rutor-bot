import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.services.matcher import TmdbMatcher
from telegram_rutor_bot.db.models import Film

@pytest.mark.asyncio
async def test_match_films_success(mocker):
    mock_session = AsyncMock()
    
    # Mock get_unlinked_films
    mock_film = MagicMock(spec=Film, id=1, name="The Matrix", year=1999, ru_name=None)
    mocker.patch("telegram_rutor_bot.services.matcher.get_unlinked_films", AsyncMock(return_value=[mock_film]))
    mocker.patch("telegram_rutor_bot.services.matcher.update_film_metadata", AsyncMock(return_value=True))
    
    matcher = TmdbMatcher(mock_session)
    matcher.tmdb = MagicMock()
    matcher.tmdb.search_movie = AsyncMock(return_value=[{"id": 603, "vote_average": 8.7, "poster_path": "/path.jpg"}])
    
    count = await matcher.match_films()
    assert count == 1
    assert matcher.tmdb.search_movie.called

@pytest.mark.asyncio
async def test_match_films_no_match(mocker):
    mock_session = AsyncMock()
    mock_film = MagicMock(spec=Film, id=2, name="Unknown Film", year=2020, ru_name=None)
    mocker.patch("telegram_rutor_bot.services.matcher.get_unlinked_films", AsyncMock(return_value=[mock_film]))
    
    matcher = TmdbMatcher(mock_session)
    matcher.tmdb = MagicMock()
    matcher.tmdb.search_movie = AsyncMock(return_value=[])
    
    count = await matcher.match_films()
    assert count == 0
