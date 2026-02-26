from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.db.models import Film
from telegram_rutor_bot.recommendations import get_recommendations, get_user_preferences


@pytest.mark.asyncio
async def test_get_user_preferences_variations(mocker):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = ['Action, Sci-Fi', 'Action', 'Drama']
    mock_session.execute = AsyncMock(return_value=mock_result)

    prefs = await get_user_preferences(mock_session)
    assert prefs['Action'] == 0.5  # 2 out of 4 total genre tags
    assert prefs['Sci-Fi'] == 0.25


@pytest.mark.asyncio
async def test_get_recommendations_with_history(mocker):
    mock_session = AsyncMock()
    mocker.patch('telegram_rutor_bot.recommendations.get_user_preferences', AsyncMock(return_value={'Action': 1.0}))

    f1 = MagicMock(spec=Film, id=1, genres='Action', rating='8.0')
    f1.name = 'Action Film'

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [f1]
    mock_session.execute = AsyncMock(return_value=mock_result)

    recs = await get_recommendations(mock_session, limit=1)
    assert len(recs) == 1
    assert recs[0].name == 'Action Film'
