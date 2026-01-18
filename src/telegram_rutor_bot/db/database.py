"""Database connection and session management"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import PoolProxiedConnection

from telegram_rutor_bot.config import settings

log = logging.getLogger(f'{settings.log_prefix}.db')


class DatabaseState:
    """Holds database connection state"""

    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self.session_maker: async_sessionmaker[AsyncSession] | None = None


db_state = DatabaseState()


def init_db() -> None:
    """Initialize database engines for both sync and async operations"""
    if hasattr(settings, 'database_url') and settings.database_url:
        # PostgreSQL for production
        async_url = str(settings.database_url).replace('postgresql://', 'postgresql+asyncpg://')
        db_state.engine = create_async_engine(async_url, echo=False)
    else:
        # SQLite for local development
        # Ensure database directory exists
        if settings.database_path:
            db_path = Path(settings.database_path)
            if db_path.parent:
                db_path.parent.mkdir(parents=True, exist_ok=True)

        async_url = f'sqlite+aiosqlite:///{settings.database_path}'
        db_state.engine = create_async_engine(async_url, echo=False)

        # Enable foreign keys for SQLite
        @event.listens_for(db_state.engine.sync_engine, 'connect')
        def set_sqlite_pragma(dbapi_connection: DBAPIConnection, _: PoolProxiedConnection) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()

    db_state.session_maker = async_sessionmaker(db_state.engine, class_=AsyncSession, expire_on_commit=False)

    # Note: Tables are now created via Alembic migrations
    # Run: uv run alembic upgrade head
    log.info('Database engines initialized: %s', async_url)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """Provide an async transactional scope around a series of operations."""
    if db_state.session_maker is None:
        raise RuntimeError('Database not initialized. Call init_db() first.')
    async with db_state.session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession]:
    """Dependency for getting async database session"""
    if db_state.session_maker is None:
        raise RuntimeError('Database not initialized. Call init_db() first.')
    async with db_state.session_maker() as session:
        yield session
