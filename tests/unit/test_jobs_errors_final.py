from unittest.mock import AsyncMock

import pytest

from telegram_rutor_bot.tasks.jobs import cleanup_torrents


@pytest.mark.asyncio
async def test_cleanup_torrents_error_path(mocker):
    # Mock client.list_torrents raising error
    mock_tc = AsyncMock()
    mock_tc.list_torrents.side_effect = Exception('Failed')
    mocker.patch('telegram_rutor_bot.tasks.jobs.get_torrent_client', return_value=mock_tc)

    # Should not raise
    await cleanup_torrents()
    assert mock_tc.list_torrents.called
