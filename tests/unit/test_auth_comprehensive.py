import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from telegram_rutor_bot.web.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token_and_get_user,
    get_current_user,
    get_current_admin_if_configured,
    get_current_active_user,
    get_current_admin_user,
    login,
    verify_tfa,
    tfa_codes,
    send_telegram_code
)
from telegram_rutor_bot.db.models import User

def test_password_utilities():
    pwd = "secret_password"
    hashed = get_password_hash(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong", hashed) is False
    assert verify_password(pwd, None) is False
    
    # Test fallback/legacy
    assert verify_password("legacy", "legacy") is True

def test_token_creation(mocker):
    mocker.patch("telegram_rutor_bot.web.auth.settings.secret_key", "test_secret")
    token = create_access_token({"sub": "user1"}, expires_delta=timedelta(minutes=5))
    assert token is not None

@pytest.mark.asyncio
async def test_verify_token_and_get_user_flows(mocker):
    mocker.patch("telegram_rutor_bot.web.auth.settings.secret_key", "test_secret")
    token = create_access_token({"sub": "user1"})
    
    mock_session = AsyncMock()
    
    # Success
    mock_user = MagicMock(spec=User, username="user1")
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_session.execute.return_value = mock_result
    
    user = await verify_token_and_get_user(token, mock_session)
    assert user.username == "user1"
    
    # User not found
    mock_result.scalars.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        await verify_token_and_get_user(token, mock_session)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Invalid token
    with pytest.raises(HTTPException):
        await verify_token_and_get_user("invalid.token.here", mock_session)

@pytest.mark.asyncio
async def test_get_current_admin_if_configured_flows(mocker):
    mock_session = AsyncMock()
    
    # Case 1: Not configured
    mocker.patch("telegram_rutor_bot.web.auth.settings.is_configured", False)
    assert await get_current_admin_if_configured(None, mock_session) is None
    
    # Case 2: Configured, no token
    mocker.patch("telegram_rutor_bot.web.auth.settings.is_configured", True)
    with pytest.raises(HTTPException) as exc:
        await get_current_admin_if_configured(None, mock_session)
    assert exc.value.status_code == 401
    
    # Case 3: Configured, not admin
    mocker.patch("telegram_rutor_bot.web.auth.settings.secret_key", "s")
    token = create_access_token({"sub": "u"})
    mock_user = MagicMock(spec=User, is_authorized=True, is_admin=False)
    mocker.patch("telegram_rutor_bot.web.auth.verify_token_and_get_user", AsyncMock(return_value=mock_user))
    
    with pytest.raises(HTTPException) as exc:
        await get_current_admin_if_configured(token, mock_session)
    assert exc.value.status_code == 403

def test_user_role_dependencies():
    # active user
    u_inactive = MagicMock(spec=User, is_authorized=False)
    with pytest.raises(HTTPException):
        get_current_active_user(u_inactive)
        
    u_active = MagicMock(spec=User, is_authorized=True)
    assert get_current_active_user(u_active) == u_active
    
    # admin user
    u_not_admin = MagicMock(spec=User, is_admin=False)
    with pytest.raises(HTTPException):
        get_current_admin_user(u_not_admin)
        
    u_admin = MagicMock(spec=User, is_admin=True)
    assert get_current_admin_user(u_admin) == u_admin

@pytest.mark.asyncio
async def test_login_flow_comprehensive(mocker):
    mocker.patch("telegram_rutor_bot.web.auth.settings.secret_key", "s")
    mock_session = AsyncMock()
    
    hashed = get_password_hash("pass")
    mock_user = MagicMock(spec=User, username="admin", password=hashed, is_authorized=True, is_admin=True, is_tfa_enabled=False)
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_session.execute.return_value = mock_result
    
    # Success login
    form = MagicMock(username="admin", password="pass")
    res = await login(form, mock_session)
    assert "access_token" in res
    
    # TFA enabled
    mock_user.is_tfa_enabled = True
    mocker.patch("telegram_rutor_bot.web.auth.send_telegram_code", AsyncMock())
    res_tfa = await login(form, mock_session)
    assert res_tfa["tfa_required"] is True
    
    # Verify TFA
    tfa_codes["admin"] = "CODE12"
    tfa_req = MagicMock(username="admin", code="CODE12")
    res_verify = await verify_tfa(tfa_req, mock_session)
    assert "access_token" in res_verify
    
    # Wrong TFA
    tfa_codes["admin"] = "CODE12"
    tfa_req.code = "WRONG"
    with pytest.raises(HTTPException):
        await verify_tfa(tfa_req, mock_session)

@pytest.mark.asyncio
async def test_send_telegram_code_mock(mocker):
    mocker.patch("telegram_rutor_bot.web.auth.settings.telegram_token", "token")
    mock_http = AsyncMock()
    mock_http.__aenter__.return_value = mock_http
    mocker.patch("httpx.AsyncClient", return_value=mock_http)
    
    await send_telegram_code(123, "CODE")
    assert mock_http.post.called
