import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram_rutor_bot.services.watchlist import select_best_torrent, check_matches
from telegram_rutor_bot.db.models import Film, Torrent

def test_select_best_torrent_empty():
    assert select_best_torrent([], MagicMock()) is None

@pytest.mark.asyncio
async def test_check_matches_empty(mocker):
    mock_session = AsyncMock()
    await check_matches(mock_session, [])
    assert not mock_session.execute.called

@pytest.mark.asyncio
async def test_check_matches_found(mocker):
    mock_session = AsyncMock()
    
    # Mock watching films
    mock_film = MagicMock(spec=Film, id=1, name="Matrix", original_title=None, watch_status="watching")
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_film]
    mock_session.execute.return_value = mock_result
    
    # Mock new torrents
    mock_torrent = MagicMock(spec=Torrent, name="The Matrix (1999) 1080p", magnet="mag1", size=1000000000)
    
    # Mock download logic to avoid network
    mocker.patch("telegram_rutor_bot.services.watchlist._download_best_torrent_for_film", AsyncMock())
    
    await check_matches(mock_session, [mock_torrent])
    assert mock_session.execute.called
