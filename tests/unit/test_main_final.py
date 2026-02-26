import sys
from unittest.mock import AsyncMock

from telegram_rutor_bot.main import main


def test_main_cli_dispatch(mocker):
    mocker.patch('telegram_rutor_bot.main.init_db')
    mocker.patch('telegram_rutor_bot.main.init_database')
    mocker.patch('telegram_rutor_bot.main.refresh_settings_from_db', AsyncMock())
    mocker.patch('multiprocessing.set_start_method')

    # scheduler
    mocker.patch.object(sys, 'argv', ['main.py', 'scheduler'])
    mocker.patch('telegram_rutor_bot.main.run_scheduler', AsyncMock())
    main()

    # api
    mocker.patch.object(sys, 'argv', ['main.py', 'api'])
    mocker.patch('uvicorn.run')
    main()

    assert True
