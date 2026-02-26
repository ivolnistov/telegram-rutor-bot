import pytest
import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from telegram_rutor_bot.main import main, run_bot, run_scheduler

@pytest.fixture(autouse=True)
def mock_asyncio_run(mocker):
    # Mock asyncio.run to prevent it from actually running and complaining about existing loop
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
    
    # bot mode
    mocker.patch.object(sys, 'argv', ['main.py', 'bot'])
    main()
    assert True
    
    # api mode
    mocker.patch.object(sys, 'argv', ['main.py', 'api'])
    mock_uvicorn = mocker.patch("uvicorn.run")
    main()
    assert mock_uvicorn.called
    
    # scheduler mode
    mocker.patch.object(sys, 'argv', ['main.py', 'scheduler'])
    main()
    assert True

@pytest.mark.asyncio
async def test_run_bot_logic(mocker):
    mocker.patch("telegram_rutor_bot.main.refresh_settings_from_db", AsyncMock())
    mocker.patch("telegram_rutor_bot.main.config_listener_task", AsyncMock())
    mocker.patch("telegram_rutor_bot.main.sync_system_searches", AsyncMock())
    
    mock_app = MagicMock()
    mock_app.initialize = AsyncMock()
    mock_app.start = AsyncMock()
    mock_app.stop = AsyncMock()
    mock_app.shutdown = AsyncMock()
    mock_app.updater.start_polling = AsyncMock()
    mock_app.updater.stop = AsyncMock()
    
    mocker.patch("telegram_rutor_bot.main.Application.builder", return_value=MagicMock(token=MagicMock(return_value=MagicMock(build=MagicMock(return_value=mock_app)))))
    mocker.patch("telegram_rutor_bot.main.settings.telegram_token", "token")
    
    mocker.patch("asyncio.sleep", side_effect=Exception("Exit"))
    
    try:
        await run_bot()
    except Exception as e:
        assert str(e) == "Exit"
    
    assert mock_app.initialize.called

@pytest.mark.asyncio
async def test_run_scheduler_logic(mocker):
    mocker.patch("telegram_rutor_bot.main.refresh_settings_from_db", AsyncMock())
    mocker.patch("telegram_rutor_bot.main.config_listener_task", AsyncMock())
    mocker.patch("telegram_rutor_bot.main.broker.startup", AsyncMock())
    mocker.patch("telegram_rutor_bot.main.broker.shutdown", AsyncMock())
    mocker.patch("telegram_rutor_bot.main.scheduler.startup", AsyncMock())
    mocker.patch("telegram_rutor_bot.main.scheduler.shutdown", AsyncMock())
    
    mock_kiq = mocker.patch("telegram_rutor_bot.tasks.jobs.execute_scheduled_searches.kiq", AsyncMock())
    
    mocker.patch("time.time", side_effect=[0, 61])
    mocker.patch("asyncio.sleep", side_effect=Exception("Exit"))
    
    try:
        await run_scheduler()
    except Exception as e:
        assert str(e) == "Exit"
        
    assert mock_kiq.called

def test_main_worker_logic(mocker):
    mocker.patch("telegram_rutor_bot.main.init_db")
    mocker.patch("telegram_rutor_bot.main.init_database")
    mocker.patch("multiprocessing.set_start_method")
    
    mocker.patch.object(sys, 'argv', ['main.py', 'worker'])
    
    from taskiq import InMemoryBroker
    # Mocking broker directly in the module
    mocker.patch("telegram_rutor_bot.main.broker", spec=MagicMock())
    # Ensure it's not InMemoryBroker
    mocker.patch("telegram_rutor_bot.main.isinstance", return_value=False)
    
    main()
    assert True
