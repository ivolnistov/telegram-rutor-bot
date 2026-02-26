from telegram_rutor_bot.db.migrate import get_alembic_config, init_database, upgrade_database


def test_migrate_full_coverage(mocker):
    # get_alembic_config
    mocker.patch('telegram_rutor_bot.db.migrate.Path.exists', return_value=True)
    mocker.patch('telegram_rutor_bot.db.migrate.Config')
    assert get_alembic_config() is not None

    # upgrade_database
    mock_command = mocker.patch('telegram_rutor_bot.db.migrate.command')
    mocker.patch('telegram_rutor_bot.db.migrate.get_alembic_config')
    upgrade_database()
    assert mock_command.upgrade.called

    # init_database
    mocker.patch('telegram_rutor_bot.db.migrate.upgrade_database')
    mock_mkdir = mocker.patch('telegram_rutor_bot.db.migrate.Path.mkdir')
    init_database()
    assert mock_mkdir.called
