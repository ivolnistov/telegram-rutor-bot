"""Pytest configuration and shared fixtures"""

import asyncio
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import ClassVar

import pytest
import pytest_asyncio
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from telegram_rutor_bot.config import Settings
from telegram_rutor_bot.db.models import Base

# Import additional configuration

fake = Faker()


@pytest.fixture(scope='session')
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_settings(temp_dir: Path) -> Settings:
    """Create test settings"""
    return Settings(
        telegram_token='test_token_123456789',
        users_white_list=[12345, 67890],
        database_path=str(temp_dir / 'test.db'),
        torrent_client='transmission',
        transmission_host='localhost',
        transmission_port=9091,
        transmission_username='test',
        transmission_password='test',
        qbittorrent_host='localhost',
        qbittorrent_port=8080,
        qbittorrent_username='admin',
        qbittorrent_password='adminadmin',
        log_level='DEBUG',
        proxy=None,
        size_limit=1024 * 1024 * 1024,  # 1GB
        timeout=30,
    )


@pytest_asyncio.fixture
async def async_engine(test_settings: Settings):
    """Create async SQLAlchemy engine for tests"""
    engine = create_async_engine(
        f'sqlite+aiosqlite:///{test_settings.database_path}',
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession]:
    """Create async database session for tests"""
    async_session_maker = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_telegram_update():
    """Create mock Telegram Update object"""

    class MockChat:
        id = 12345
        type = 'private'

    class MockUser:
        id = 12345
        username = 'testuser'
        first_name = 'Test'
        last_name = 'User'
        is_bot = False

    class MockMessage:
        text = '/start'
        chat = MockChat()
        from_user = MockUser()
        message_id = 1
        date = fake.date_time()

    class MockUpdate:
        message = MockMessage()
        effective_chat = MockChat()
        effective_user = MockUser()

    return MockUpdate()


@pytest.fixture
def mock_context():
    """Create mock Telegram context"""

    class MockBot:
        async def send_message(self, chat_id, text, **kwargs):
            return {'chat_id': chat_id, 'text': text}

    class MockContext:
        bot = MockBot()
        user_data: ClassVar[dict] = {}
        chat_data: ClassVar[dict] = {}

    return MockContext()


@pytest.fixture
def sample_torrent_data():
    """Sample torrent data for testing"""
    return {
        'name': 'Test Movie (2023) 1080p',
        'magnet': f'magnet:?xt=urn:btih:{fake.sha256()}&dn=Test+Movie',
        'link': '/torrent/123456/test-movie-2023-1080p',
        'size': 1024 * 1024 * 1024 * 2,  # 2GB
        'seeds': 42,
        'peers': 10,
    }


@pytest.fixture
def sample_search_url():
    """Sample search URL for testing"""
    return 'http://rutor.info/search/0/0/100/0/matrix'


@pytest.fixture
def sample_rutor_html():
    """Sample HTML from rutor.info for testing parser"""
    return """
    <html>
    <body>
        <table>
            <tr>
                <td>15&nbsp;Dec&nbsp;23</td>
                <td>
                    <a href="/torrent/123456/matrix-1999-1080p">Matrix (1999) 1080p</a>
                </td>
                <td>
                    <a href="magnet:?xt=urn:btih:abcdef123456&dn=Matrix">
                        <img src="/magnet.gif">
                    </a>
                </td>
                <td>42</td>
                <td>10</td>
                <td>15.2&nbsp;GB</td>
            </tr>
        </table>
    </body>
    </html>
    """
