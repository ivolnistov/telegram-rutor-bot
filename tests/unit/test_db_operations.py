"""Unit tests for database operations"""

from datetime import UTC, datetime

import pytest

from telegram_rutor_bot.db.films import get_films, get_films_by_ids, get_or_create_film
from telegram_rutor_bot.db.searches import add_search_to_db, delete_search, get_search, get_searches
from telegram_rutor_bot.db.torrents import add_torrent, get_torrent_by_id, modify_torrent
from telegram_rutor_bot.db.users import get_or_create_user_by_chat_id


@pytest.mark.asyncio
class TestFilmOperations:
    """Test film database operations"""

    async def test_get_or_create_film_creates_new(self, async_session):
        """Test creating a new film"""
        blake = 'test_blake_123'
        year = 2023
        name = 'Test Movie'

        film = await get_or_create_film(
            async_session,
            blake=blake,
            year=year,
            name=name,
            ru_name='Тестовый фильм',
            poster='http://example.com/poster.jpg',
            rating='8.5',
        )

        assert film.id is not None
        assert film.blake == blake
        assert film.year == year
        assert film.name == name
        assert film.ru_name == 'Тестовый фильм'
        assert film.poster == 'http://example.com/poster.jpg'
        assert film.rating == '8.5'

    async def test_get_or_create_film_returns_existing(self, async_session):
        """Test that existing film is returned"""
        blake = 'existing_blake'

        # Create film first
        original = await get_or_create_film(async_session, blake=blake, year=2022, name='Original Movie')

        # Try to create again with same blake
        duplicate = await get_or_create_film(
            async_session,
            blake=blake,
            year=2023,  # Different year
            name='Different Name',
        )

        assert duplicate.id == original.id
        assert duplicate.blake == blake
        assert duplicate.year == 2022  # Original year preserved
        assert duplicate.name == 'Original Movie'  # Original name preserved

    async def test_get_films(self, async_session):
        """Test getting list of films"""
        # Create some test films
        for i in range(5):
            await get_or_create_film(async_session, blake=f'blake_{i}', year=2020 + i, name=f'Movie {i}')

        films = await get_films(async_session, limit=3)

        assert len(films) == 3
        # Should be ordered by ID descending
        # The exact order depends on IDs, but we should have 3 films
        film_names = {f.name for f in films}
        assert len(film_names) == 3

    async def test_get_films_by_ids(self, async_session):
        """Test getting films by IDs"""
        # Create test films
        film1 = await get_or_create_film(async_session, blake='blake1', name='Film 1', year=2021)
        await get_or_create_film(async_session, blake='blake2', name='Film 2', year=2022)
        film3 = await get_or_create_film(async_session, blake='blake3', name='Film 3', year=2023)

        films = await get_films_by_ids(async_session, [film1.id, film3.id])

        assert len(films) == 2
        film_names = {f.name for f in films}
        assert 'Film 1' in film_names
        assert 'Film 3' in film_names
        assert 'Film 2' not in film_names


@pytest.mark.asyncio
class TestTorrentOperations:
    """Test torrent database operations"""

    async def test_add_torrent(self, async_session):
        """Test adding a new torrent"""
        # Create a film first
        film = await get_or_create_film(async_session, blake='film_blake', name='Test Film', year=2023)

        torrent = await add_torrent(
            async_session,
            film_id=film.id,
            blake='torrent_blake',
            name='Test.Film.2023.1080p',
            magnet='magnet:?xt=urn:btih:123456',
            link='/torrent/123456',
            sz=1024 * 1024 * 1024,  # 1GB
            created=datetime(2023, 1, 1, tzinfo=UTC),
            approved=True,
            downloaded=False,
        )

        assert torrent.id is not None
        assert torrent.film_id == film.id
        assert torrent.blake == 'torrent_blake'
        assert torrent.name == 'Test.Film.2023.1080p'
        assert torrent.size == 1024 * 1024 * 1024

    async def test_add_torrent_duplicate_blake_returns_existing(self, async_session):
        """Test that duplicate blake returns existing torrent"""
        film = await get_or_create_film(async_session, blake='film_blake', name='Test Film', year=2023)

        # Add first torrent
        original = await add_torrent(
            async_session,
            film_id=film.id,
            blake='duplicate_blake',
            name='Original',
            magnet='magnet:?xt=urn:btih:111111',
            link='/torrent/111111',
            sz=1000,
        )

        # Try to add with same blake
        duplicate = await add_torrent(
            async_session,
            film_id=film.id,
            blake='duplicate_blake',
            name='Different',
            magnet='magnet:?xt=urn:btih:222222',
            link='/torrent/222222',
            sz=2000,
        )

        assert duplicate.id == original.id
        assert duplicate.name == 'Original'

    async def test_get_torrent_by_id(self, async_session):
        """Test getting torrent by ID"""
        film = await get_or_create_film(async_session, blake='film_blake', name='Test Film', year=2023)

        torrent = await add_torrent(
            async_session,
            film_id=film.id,
            blake='test_blake',
            name='Test Torrent',
            magnet='magnet:?xt=urn:btih:abcdef',
            link='/torrent/abcdef',
            sz=500000,
        )

        fetched = await get_torrent_by_id(async_session, torrent.id)

        assert fetched is not None
        assert fetched.id == torrent.id
        assert fetched.name == 'Test Torrent'
        # Check that film relationship is loaded
        assert fetched.film is not None
        assert fetched.film.name == 'Test Film'

    async def test_modify_torrent(self, async_session):
        """Test modifying torrent attributes"""
        film = await get_or_create_film(async_session, blake='film_blake', name='Test Film', year=2023)

        torrent = await add_torrent(
            async_session,
            film_id=film.id,
            blake='test_blake',
            name='Original Name',
            magnet='magnet:?xt=urn:btih:123456',
            link='/torrent/123456',
            sz=1000,
            approved=False,
            downloaded=False,
        )

        # Modify torrent
        success = await modify_torrent(
            async_session, torrent_id=torrent.id, name='Updated Name', sz=2000, approved=True, downloaded=True
        )

        assert success is True

        # Fetch and verify
        updated = await get_torrent_by_id(async_session, torrent.id)
        assert updated.name == 'Updated Name'
        assert updated.size == 2000
        assert updated.approved is True
        assert updated.downloaded is True


@pytest.mark.asyncio
class TestUserOperations:
    """Test user database operations"""

    async def test_get_or_create_user_by_chat_id_creates_new(self, async_session):
        """Test creating a new user"""
        chat_id = 123456789
        name = 'Test User'
        username = 'testuser'

        user = await get_or_create_user_by_chat_id(async_session, chat_id=chat_id, name=name, username=username)

        assert user.id is not None
        assert user.chat_id == chat_id
        assert user.name == name
        assert user.username == username

    async def test_get_or_create_user_by_chat_id_returns_existing(self, async_session):
        """Test that existing user is returned"""
        chat_id = 987654321

        # Create user first
        original = await get_or_create_user_by_chat_id(
            async_session, chat_id=chat_id, name='Original Name', username='original'
        )

        # Try to create again with same chat_id
        duplicate = await get_or_create_user_by_chat_id(
            async_session, chat_id=chat_id, name='Different Name', username='different'
        )

        assert duplicate.id == original.id
        assert duplicate.chat_id == chat_id
        # Updated fields should be preserved
        assert duplicate.name == 'Different Name'
        assert duplicate.username == 'different'


@pytest.mark.asyncio
class TestSearchOperations:
    """Test search database operations"""

    async def test_add_search_to_db(self, async_session):
        """Test adding a new search"""
        # Create a user first
        user = await get_or_create_user_by_chat_id(async_session, chat_id=12345)

        search_id = await add_search_to_db(
            async_session, url='http://rutor.info/search/0/0/100/0/matrix', cron='0 * * * *', creator_id=user.id
        )

        assert search_id is not None

        # Verify search was created
        search = await get_search(async_session, search_id)
        assert search is not None
        assert search.url == 'http://rutor.info/search/0/0/100/0/matrix'
        assert search.cron == '0 * * * *'
        assert search.creator_id == user.id

    async def test_add_search_duplicate_url_raises_error(self, async_session):
        """Test that duplicate URL raises error"""
        user = await get_or_create_user_by_chat_id(async_session, chat_id=12345)
        duplicate_url = 'http://rutor.info/search/duplicate'

        # Add first search
        await add_search_to_db(async_session, url=duplicate_url, cron='* * * * *', creator_id=user.id)

        # Try to add duplicate
        with pytest.raises(ValueError, match='already exists'):
            await add_search_to_db(async_session, url=duplicate_url, cron='0 * * * *', creator_id=user.id)

    async def test_get_searches(self, async_session):
        """Test getting all searches"""
        user = await get_or_create_user_by_chat_id(async_session, chat_id=12345)

        # Add some searches
        for i in range(3):
            await add_search_to_db(
                async_session, url=f'http://rutor.info/search/{i}', cron='* * * * *', creator_id=user.id
            )

        searches = await get_searches(async_session, show_empty=True)

        assert len(searches) == 3

    async def test_delete_search(self, async_session):
        """Test deleting a search"""
        user = await get_or_create_user_by_chat_id(async_session, chat_id=12345)

        search_id = await add_search_to_db(
            async_session, url='http://rutor.info/search/to_delete', cron='* * * * *', creator_id=user.id
        )

        # Delete the search
        success = await delete_search(async_session, search_id)
        assert success is True

        # Verify it's deleted
        search = await get_search(async_session, search_id)
        assert search is None
