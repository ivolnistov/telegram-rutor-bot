from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from telegram_rutor_bot.db.models import User
from telegram_rutor_bot.web.auth import get_password_hash, login


@pytest.mark.asyncio
async def test_login_incorrect_password_final(mocker):
    hashed = get_password_hash('pass')
    mock_user = MagicMock(spec=User, username='admin', password=hashed, is_authorized=True)

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    form = MagicMock(username='admin', password='wrong_password')

    with pytest.raises(HTTPException) as e:
        await login(form, mock_session)
    assert e.value.status_code == 400


@pytest.mark.asyncio
async def test_login_user_not_found(mocker):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    form = MagicMock(username='nonexistent', password='p')
    with pytest.raises(HTTPException) as e:
        await login(form, mock_session)
    assert e.value.status_code == 400
