import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.main import main, run_scheduler


@pytest.fixture(autouse=True)
def mock_asyncio_run(mocker):
    return mocker.patch("asyncio.run")

def test_main_arg_parsing(mocker):
    mocker.patch.object(sys, 'argv', ['main.py', '--help'])
    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 0

def test_main_dispatch_modes(mocker):
    mocker.patch("telegram_rutor_bot.main.init_db")
    mocker.patch("telegram_rutor_bot.main.init_database")
    mocker.patch("telegram_rutor_bot.main.refresh_settings_from_db", AsyncMock())
    mocker.patch("multiprocessing.set_start_method")

    mocker.patch.object(sys, 'argv', ['main.py', 'bot'])
    main()
    assert True

    mocker.patch.object(sys, 'argv', ['main.py', 'api'])
    mock_uvicorn = mocker.patch("uvicorn.run")
    main()
    assert mock_uvicorn.called

@pytest.mark.asyncio
async def test_run_scheduler_logic(mocker):
    mocker.patch("telegram_rutor_bot.main.refresh_settings_from_db", AsyncMock())
    mocker.patch("telegram_rutor_bot.main.config_listener_task", AsyncMock())
    mocker.patch("telegram_rutor_bot.main.broker.startup", AsyncMock())
    mocker.patch("telegram_rutor_bot.main.scheduler.startup", AsyncMock())

    mock_kiq = mocker.patch("telegram_rutor_bot.tasks.jobs.execute_scheduled_searches.kiq", AsyncMock())

    mocker.patch("time.time", side_effect=[0, 61, 122])
    mocker.patch("asyncio.sleep", side_effect=[None, Exception("Exit")])

    try:
        await run_scheduler()
    except Exception as e:
        if str(e) != "Exit":
            raise

    assert mock_kiq.called

def test_main_worker_logic(mocker):
    mocker.patch("telegram_rutor_bot.main.init_db")
    mocker.patch("telegram_rutor_bot.main.init_database")
    mocker.patch("multiprocessing.set_start_method")

    mocker.patch.object(sys, 'argv', ['main.py', 'worker'])

    mocker.patch("telegram_rutor_bot.main.broker", MagicMock())
    mocker.patch("telegram_rutor_bot.main.isinstance", return_value=False)

    main()
    assert True
