import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from telegram_rutor_bot.web.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    verify_token_and_get_user,
    login,
    verify_tfa,
    tfa_codes
)
from telegram_rutor_bot.db.models import User

def test_auth_utils():
    h = get_password_hash("p")
    assert verify_password("p", h) is True
    assert verify_password("w", h) is False
    assert create_access_token({"sub": "u"}) is not None

@pytest.mark.asyncio
async def test_verify_token_and_get_user_full(mocker):
    mocker.patch("telegram_rutor_bot.web.auth.settings.secret_key", "s")
    token = create_access_token({"sub": "u"})
    
    mock_session = AsyncMock()
    mock_user = MagicMock(spec=User, username="u", is_authorized=True)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    user = await verify_token_and_get_user(token, mock_session)
    assert user.username == "u"

@pytest.mark.asyncio
async def test_login_and_tfa_full(mocker):
    mocker.patch("telegram_rutor_bot.web.auth.settings.secret_key", "s")
    mocker.patch("telegram_rutor_bot.web.auth.settings.telegram_token", "t")
    
    hashed = get_password_hash("p")
    mock_user = MagicMock(spec=User, username="u", password=hashed, is_authorized=True, is_admin=True, is_tfa_enabled=True, chat_id=123)
    
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # login
    form = MagicMock(username="u", password="p")
    mocker.patch("telegram_rutor_bot.web.auth.send_telegram_code", AsyncMock())
    res = await login(form, mock_session)
    assert res["tfa_required"] is True
    
    # verify_tfa
    tfa_codes["u"] = "123456"
    req = MagicMock(username="u", code="123456")
    res_tfa = await verify_tfa(req, mock_session)
    assert "access_token" in res_tfa
