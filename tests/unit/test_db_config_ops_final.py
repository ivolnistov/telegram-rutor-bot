import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_rutor_bot.db.config_ops import get_db_config, update_db_config
from telegram_rutor_bot.db.models import AppConfig


@pytest.mark.asyncio
async def test_config_ops_full(async_session: AsyncSession):
    # get_db_config (creates if not exists)
    config = await get_db_config(async_session)
    assert config is not None
    assert config.id == 1

    # update_db_config
    res = await update_db_config(async_session, telegram_token='new_token', is_configured=True)
    assert isinstance(res, AppConfig)
    assert res.telegram_token == 'new_token'

    # verify update
    config2 = await get_db_config(async_session)
    assert config2.telegram_token == 'new_token'
    assert config2.is_configured is True

    # update with no args
    res3 = await update_db_config(async_session)
    assert res3.id == 1
