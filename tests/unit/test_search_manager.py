from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from telegram_rutor_bot.config import SearchConfig
from telegram_rutor_bot.services.search_manager import _substitute_variables, sync_system_searches


@pytest.fixture
def mock_settings():
    with patch('telegram_rutor_bot.services.search_manager.settings') as mock:
        yield mock


@pytest.fixture
def mock_session():
    mock = MagicMock()

    # Mock execute to return a result that has scalars().first()
    # execute is async, so it returns an awaitable
    async def _execute(*args, **kwargs):
        result = MagicMock()
        result.scalars.return_value.first.return_value = None
        result.scalars.return_value.all.return_value = []
        return result

    mock.execute.side_effect = _execute

    # Mock commit
    async def _commit():
        pass

    mock.commit.side_effect = _commit

    return mock


@pytest.fixture
def mock_get_async_session(mock_session):
    with patch('telegram_rutor_bot.services.search_manager.get_async_session') as mock:
        mock.return_value.__aenter__.return_value = mock_session
        yield mock


def test_substitute_variables():
    # Freeze time for consistent testing
    fixed_now = datetime(2024, 5, 15, 12, 0, 0, tzinfo=UTC)

    with patch('telegram_rutor_bot.services.search_manager.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_now

        url = 'http://rutor.info/year:{year}/month:{month}'
        result = _substitute_variables(url)
        assert result == 'http://rutor.info/year:2024/month:05'

        url = 'prev:{prev_year}/next:{next_year}'
        result = _substitute_variables(url)
        assert result == 'prev:2023/next:2025'

        # Test edge case month wrapping if complex logic used (but current impl is simple)
        # {prev_month} for May (5) should be March (3)? Or April (4)?
        # Implementation says: (now.month - 2) % 12 + 1
        # 5 - 2 = 3. % 12 = 3. + 1 = 4. Correct (April is prev month of May)
        # Wait, usually prev_month of May is April (4).
        # (5 - 2) % 12 + 1:
        # If month=1 (Jan): (1-2)=-1. -1 % 12 = 11. 11+1=12 (Dec). Correct.
        # If month=5 (May): 3 % 12 = 3. + 1 = 4 (April). Correct.

        url = '{prev_month}-{month}-{next_month}'
        result = _substitute_variables(url)
        assert result == '04-05-06'


@pytest.mark.asyncio
async def test_sync_system_searches(mock_settings, mock_get_async_session, mock_session):
    # Setup
    mock_settings.searches = [SearchConfig(name='Test Search', url='http://test.url/{year}', cron='0 * * * *')]

    # Mock existing searches -> None
    mock_session.execute.return_value.scalars.return_value.first.return_value = None

    # Run
    await sync_system_searches()

    # Verify
    assert mock_session.add.called
    args = mock_session.add.call_args[0]
    search = args[0]
    assert search.query == 'Test Search'  # We decided to use query for name
    assert '2024' in search.url or '{year}' not in search.url  # Depends on if we mocked time or run real
