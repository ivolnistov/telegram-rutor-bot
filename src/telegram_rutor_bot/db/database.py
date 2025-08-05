"""Database connection and session management"""

import logging
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import PoolProxiedConnection

from telegram_rutor_bot.config import settings

log = logging.getLogger(f'{settings.log_prefix}.db')

# Sync engine for migrations
engine: Engine | None = None
SessionLocal: sessionmaker | None = None

# Async engine for new async code
async_engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def init_db() -> None:
    """Initialize database engines for both sync and async operations"""
    # COMMENT: Need global to modify module-level database connection instances
    global engine, SessionLocal, async_engine, AsyncSessionLocal  # noqa: PLW0603 pylint: disable=global-statement

    if hasattr(settings, 'database_url') and settings.database_url:
        # PostgreSQL for production
        sync_url = settings.database_url
        async_url = str(settings.database_url).replace('postgresql://', 'postgresql+asyncpg://')

        engine = create_engine(sync_url)
        async_engine = create_async_engine(async_url, echo=False)
    else:
        # SQLite for local development
        sync_url = f'sqlite:///{settings.database_path}'
        async_url = f'sqlite+aiosqlite:///{settings.database_path}'

        engine = create_engine(sync_url, connect_args={'check_same_thread': False})

        # Enable foreign keys for SQLite
        @event.listens_for(Engine, 'connect')
        def set_sqlite_pragma(dbapi_connection: DBAPIConnection, _: PoolProxiedConnection) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()

        async_engine = create_async_engine(async_url, echo=False)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    # Note: Tables are now created via Alembic migrations
    # Run: uv run alembic upgrade head
    log.info('Database engines initialized: %s', sync_url)


@contextmanager
def get_session() -> Generator[Session]:
    """Provide a transactional scope around a series of operations."""
    if SessionLocal is None:
        raise RuntimeError('Database not initialized. Call init_db() first.')
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """Provide an async transactional scope around a series of operations."""
    if AsyncSessionLocal is None:
        raise RuntimeError('Database not initialized. Call init_db() first.')
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db() -> Generator[Session]:
    """Dependency for getting database session (sync)"""
    if SessionLocal is None:
        raise RuntimeError('Database not initialized. Call init_db() first.')
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession]:
    """Dependency for getting async database session"""
    if AsyncSessionLocal is None:
        raise RuntimeError('Database not initialized. Call init_db() first.')
    async with AsyncSessionLocal() as session:
        yield session
