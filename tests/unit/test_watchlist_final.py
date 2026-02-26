import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram import Update
from telegram_rutor_bot.handlers.watchlist import watch_command, _parse_watch_args

@pytest.mark.asyncio
async def test_watch_command_flow(mocker):
    update = MagicMock(spec=Update)
    update.effective_chat.id = 123
    update.message.text = "/watch Matrix min:10 max:20"
    
    mock_user = MagicMock(is_authorized=True)
    mocker.patch("telegram_rutor_bot.utils.security.get_or_create_user_by_chat_id", AsyncMock(return_value=mock_user))
    
    # Mock session and DB results
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    mocker.patch("telegram_rutor_bot.handlers.watchlist.get_async_session", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))
    
    mocker.patch("telegram_rutor_bot.handlers.watchlist.search_film_on_rutor.kiq", AsyncMock())
    
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    
    await watch_command(update, context)
    assert context.bot.send_message.called

def test_parse_watch_args_extended():
    n, p = _parse_watch_args("Name voice:LostFilm min:1 max:2 size:1.5")
    assert n == "Name"
    assert p["voice"] == "LostFilm"
    assert p["min"] == 1.0
    assert p["max"] == 2.0
    assert p["size"] == 1.5
