"""Database migration utilities using Alembic"""

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from telegram_rutor_bot.config import settings

log = logging.getLogger(f'{settings.log_prefix}.migrate')


def get_alembic_config() -> Config:
    """Get Alembic configuration"""
    # Find alembic.ini from the project root
    project_root = Path(__file__).parent.parent.parent.parent
    alembic_ini = project_root / 'alembic.ini'

    if not alembic_ini.exists():
        raise FileNotFoundError(f'alembic.ini not found at {alembic_ini}')

    return Config(str(alembic_ini))


def upgrade_database() -> None:
    """Run database migrations to the latest version"""
    config = get_alembic_config()

    try:
        log.info('Running database migrations...')
        command.upgrade(config, 'head')
        log.info('Database migrations completed successfully')
    except Exception as e:
        log.error('Failed to run migrations: %s', e)
        raise


def check_current_revision() -> None:
    """Check the current database revision"""
    config = get_alembic_config()

    try:
        command.current(config)
    except Exception as e:
        log.error('Failed to check current revision: %s', e)
        raise


def init_database() -> None:
    """Initialize database with migrations"""
    # Create database directory if it doesn't exist
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Run migrations
    upgrade_database()
