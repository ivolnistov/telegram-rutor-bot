from unittest.mock import AsyncMock

import pytest

from telegram_rutor_bot.tasks.jobs import cleanup_torrents


@pytest.mark.asyncio
async def test_cleanup_torrents_loop(mocker):
    # Mock client with torrents to cleanup
    mock_tc = AsyncMock()
    mock_tc.list_torrents.return_value = [
        {'hash': 'h1', 'status': 'pausedup', 'name': 'T1'},  # Should be removed
        {'hash': 'h2', 'status': 'downloading', 'name': 'T2'},  # Should stay
    ]
    mocker.patch('telegram_rutor_bot.tasks.jobs.get_torrent_client', return_value=mock_tc)

    await cleanup_torrents()
    assert mock_tc.remove_torrent.called
    mock_tc.remove_torrent.assert_called_with('h1')
