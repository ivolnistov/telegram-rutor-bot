from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from telegram_rutor_bot.web.app import app

client = TestClient(app)


def test_app_more_get_endpoints(mocker):
    from telegram_rutor_bot.web.auth import get_current_admin_user

    app.dependency_overrides[get_current_admin_user] = lambda: MagicMock(is_admin=True)

    mocker.patch(
        'telegram_rutor_bot.web.app.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=AsyncMock()), __aexit__=AsyncMock()),
    )

    # Mock return for tasks
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mocker.patch(
        'telegram_rutor_bot.web.app.get_async_session',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()),
    )

    client.get('/api/tasks')
    client.get('/api/torrents')
    client.get('/api/films')

    # Mock torrent client
    mock_tc = AsyncMock()
    mock_tc.list_torrents.return_value = []
    mocker.patch('telegram_rutor_bot.web.app.get_torrent_client', return_value=mock_tc)
    client.get('/api/downloads')

    app.dependency_overrides = {}
