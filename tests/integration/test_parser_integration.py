"""Integration tests for rutor parser"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from telegram_rutor_bot.db.films import get_films_by_ids
from telegram_rutor_bot.rutor.parser import (
    get_torrent_info,
    has_good_link,
    parse_name,
    parse_rutor,
    size_to_bytes_converter,
)
from telegram_rutor_bot.rutor.rating_parser import get_movie_ratings


@pytest.mark.integration
class TestRutorParserIntegration:
    """Integration tests for rutor parser"""

    @pytest.fixture
    def mock_rutor_search_html(self):
        """Mock HTML response for rutor search page"""
        return """
        <html>
        <body>
            <table>
                <tr>
                    <td>15&nbsp;Dec&nbsp;23</td>
                    <td>
                        <a href="/torrent/123456/matrix-1999-1080p">Matrix (1999) 1080p</a>
                        <a href="magnet:?xt=urn:btih:abcdef123456&dn=Matrix">
                            <img src="/magnet.gif">
                        </a>
                    </td>
                    <td>42</td>
                    <td>10</td>
                    <td>15.2&nbsp;GB</td>
                </tr>
                <tr>
                    <td>14&nbsp;Dec&nbsp;23</td>
                    <td>
                        <a href="/torrent/123457/matrix-reloaded-2003-1080p">Matrix Reloaded (2003) 1080p</a>
                        <a href="magnet:?xt=urn:btih:abcdef123457&dn=Matrix+Reloaded">
                            <img src="/magnet.gif">
                        </a>
                    </td>
                    <td>38</td>
                    <td>8</td>
                    <td>16.5&nbsp;GB</td>
                </tr>
            </table>
        </body>
        </html>
        """

    @pytest.fixture
    def mock_torrent_page_html(self):
        """Mock HTML response for torrent details page"""
        return """
        <html>
        <head>
            <title>Matrix (1999) 1080p BluRay :: rutor.info</title>
        </head>
        <body>
            <div id="details">
                <table>
                    <!-- Movie info header row -->
                    <tr>
                        <td>Название:</td>
                        <td>Матрица</td>
                    </tr>
                    <tr>
                        <td>Оригинальное название:</td>
                        <td>The Matrix</td>
                    </tr>
                    <tr>
                        <td>Год выпуска:</td>
                        <td>1999</td>
                    </tr>
                    <tr>
                        <td>Жанр:</td>
                        <td>Фантастика, Боевик</td>
                    </tr>
                    <tr>
                        <td>Страна:</td>
                        <td>США, Австралия</td>
                    </tr>
                    <tr>
                        <td>Продолжительность:</td>
                        <td>136 мин. / 02:16</td>
                    </tr>
                    <tr>
                        <td>Режиссер:</td>
                        <td>Лана Вачовски, Лилли Вачовски</td>
                    </tr>
                    <tr>
                        <td>В ролях:</td>
                        <td>Киану Ривз, Лоуренс Фишберн, Кэрри-Энн Мосс</td>
                    </tr>
                    <tr>
                        <td>Описание:</td>
                        <td>Хакер Нео узнает, что его мир — иллюзия.</td>
                    </tr>
                    <tr>
                        <td>Видео:</td>
                        <td>1920x1080, 23.976 fps, 10000 kbps</td>
                    </tr>
                    <tr>
                        <td>Аудио:</td>
                        <td>DTS-HD MA 5.1, 48 kHz</td>
                    </tr>
                    <tr>
                        <td>Перевод:</td>
                        <td>Профессиональный (многоголосый)</td>
                    </tr>
                </table>
            </div>
            <a href="https://www.imdb.com/title/tt0133093/">IMDB</a>
            <a href="https://www.kinopoisk.ru/film/301/">Кинопоиск</a>
            <img src="//fastpic.org/images/2023/matrix_poster.jpg" />
            <img src="//fastpic.org/images/2023/matrix_screen1.jpg" />
        </body>
        </html>
        """

    @pytest.mark.asyncio
    async def test_parse_rutor_search_page(self, async_session, mock_rutor_search_html):
        """Test parsing rutor search results"""
        with patch('telegram_rutor_bot.rutor.parser._get_client') as mock_client:
            # Setup mock response
            mock_response = Mock()
            mock_response.text = mock_rutor_search_html
            mock_response.raise_for_status = Mock()

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.__aexit__.return_value = None

            mock_client.return_value = mock_async_client

            # Mock localize context manager
            with patch('telegram_rutor_bot.rutor.parser.localize'):
                # Parse the page
                url = 'http://rutor.info/search/0/0/100/0/matrix'
                new_films = await parse_rutor(url, async_session)

            # Verify results
            assert len(new_films) == 2

            # Check that films were created
            films = await get_films_by_ids(async_session, new_films)
            assert len(films) == 2

            # Check film details
            matrix_film = next((f for f in films if 'Matrix' in f.name and f.year == 1999), None)
            assert matrix_film is not None
            assert matrix_film.year == 1999

    @pytest.mark.asyncio
    async def test_get_torrent_info(self, mock_torrent_page_html):
        """Test getting detailed torrent info"""
        with patch('telegram_rutor_bot.rutor.parser._get_client') as mock_client:
            # Setup mock response
            mock_response = Mock()
            mock_response.text = mock_torrent_page_html
            mock_response.raise_for_status = Mock()
            mock_response.content = b'fake_image_data'

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.__aexit__.return_value = None

            mock_client.return_value = mock_async_client

            # Mock cache to prevent caching issues
            with patch('telegram_rutor_bot.rutor.parser.FilmInfoCache') as mock_cache_class:
                mock_cache = Mock()
                mock_cache.get.return_value = None  # No cached data
                mock_cache.set.return_value = None
                mock_cache_class.return_value = mock_cache

                # Mock rating parser - patch where it's imported in parser module
                with patch('telegram_rutor_bot.rutor.parser.get_movie_ratings') as mock_ratings:
                    mock_ratings.return_value = ('8.7', '8.5')

                    # Get torrent info
                    message, poster, images, _, _ = await get_torrent_info('/torrent/123456/matrix-1999-1080p')

            # Verify message content
            assert '🎬 The Matrix (1999)' in message  # Title from page title
            assert 'Матрица' in message or 'The Matrix' in message
            # Check for ratings - they should be on the same line if both present
            if '⭐ Кинопоиск: 8.5/10' in message:
                assert '⭐ IMDB: 8.7/10 | ⭐ Кинопоиск: 8.5/10' in message
            else:
                # If no Kinopoisk rating, just check IMDB
                assert '⭐ IMDB: 8.7/10' in message
            assert '📁 Жанр: Фантастика, Боевик' in message
            assert '🌍 Страна: США, Австралия' in message
            assert '⏱ Продолжительность: 136 мин. / 02:16' in message
            assert '🎭 Режиссер: Лана Вачовски, Лилли Вачовски' in message
            assert '👥 В ролях: Киану Ривз' in message
            assert '📝 Описание:' in message
            assert 'Хакер Нео узнает' in message
            assert '📹 Видео: 1920x1080' in message
            # Check for either audio tracks or translation
            if '🎙 Аудио' in message:
                # If audio tracks are present, translation won't be shown
                assert '🎙 Аудио' in message
            else:
                assert '🎙 Перевод: Профессиональный' in message
            assert '🔗 IMDB: https://www.imdb.com/title/tt0133093/' in message
            assert '🔗 Кинопоиск: https://www.kinopoisk.ru/film/301/' in message

            # Verify images - first image usually becomes poster, rest are screenshots
            assert poster is not None or len(images) > 0
            # Total images (poster + screenshots) should match what's in HTML
            total_images = (1 if poster else 0) + len(images)
            assert total_images <= 3  # Parser limits to 3 images

    @pytest.mark.asyncio
    async def test_get_movie_ratings_mock(self):
        """Test getting movie ratings with mocked responses"""
        # Mock IMDB response
        imdb_html = """
        <html>
        <body>
            <div data-testid="hero-rating-bar__aggregate-rating__score">
                <span>8.7</span>
            </div>
        </body>
        </html>
        """

        # Mock Kinopoisk response
        kp_html = """
        <html>
        <body>
            <span class="film-rating-value">8.5</span>
        </body>
        </html>
        """

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()

            # Setup responses
            imdb_response = Mock()
            imdb_response.text = imdb_html
            imdb_response.raise_for_status = Mock()

            kp_response = Mock()
            kp_response.text = kp_html
            kp_response.raise_for_status = Mock()

            # Configure mock to return different responses based on URL
            async def mock_get(url, **kwargs):
                if 'imdb.com' in url:
                    return imdb_response
                if 'kinopoisk.ru' in url:
                    return kp_response
                return Mock()

            mock_client.get = mock_get
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            mock_client_class.return_value = mock_client

            # Get ratings
            imdb_rating, kp_rating = await get_movie_ratings(
                'https://www.imdb.com/title/tt0133093/', 'https://www.kinopoisk.ru/film/301/'
            )

            assert imdb_rating == '8.7'
            assert kp_rating == '8.5'


class TestParserUtilities:
    """Test parser utility functions"""

    def test_parse_name(self):
        """Test movie name parsing"""
        # Test with year in parentheses
        name, year = parse_name('The Matrix (1999) 1080p BluRay')
        assert name == 'The Matrix'
        assert year == '1999'

        # Test with brackets
        name, year = parse_name('The Matrix (1999) [Extended Cut] / Матрица')
        assert name == 'The Matrix'
        assert year == '1999'

        # Test without year
        name, year = parse_name('Some Movie Title')
        assert name == 'Some Movie Title'
        assert year == str(datetime.now(UTC).year)  # Current year

    def test_size_to_bytes_converter(self):
        """Test file size conversion"""
        assert size_to_bytes_converter('1.5 GB') == int(1.5 * 1024 * 1024 * 1024)
        assert size_to_bytes_converter('750 MB') == (750 * 1024 * 1024)
        assert size_to_bytes_converter('500 KB') == (500 * 1024)
        assert size_to_bytes_converter('invalid') == 0

    def test_has_good_link(self):
        """Test link validation"""
        assert has_good_link('https://www.imdb.com/title/tt0133093/') is True
        assert has_good_link('https://www.kinopoisk.ru/film/301/') is True
        assert has_good_link('https://example.com') is False
        assert has_good_link('not a url') is False


@pytest.mark.integration
@pytest.mark.external
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'search_url',
    [
        'http://rutor.info/search/0/0/100/0/matrix',
        'http://rutor.info/search/0/1/100/0/2024%201080p',
        'http://rutor.info/search/0/0/100/0/avatar',
    ],
)
async def test_real_rutor_search(async_session, search_url):
    """Test with real rutor search page (requires internet connection)"""
    # Skip if offline or in CI
    pytest.skip('Skipping external API test')

    try:
        new_films = await parse_rutor(search_url, async_session)

        # Basic assertions
        assert isinstance(new_films, list)
        if new_films:
            # Check that films were created
            films = await get_films_by_ids(async_session, new_films)
            assert len(films) > 0

            # Check film properties
            for film in films:
                assert film.id is not None
                assert film.name is not None
                assert film.blake is not None
    except httpx.ConnectError:
        pytest.skip('Cannot connect to rutor.info')


@pytest.mark.integration
@pytest.mark.external
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'torrent_data',
    [
        {
            'link': '/torrent/840427/mama-vozvrawenie-iz-tmy_the-unlit-2020-web-dl-1080p-itunes',
            'expected_title': 'Мама: Возвращение из тьмы',
            'expected_year': '2020',
            'has_imdb': True,
            'has_kp': True,
        },
        {
            'link': '/torrent/984321/avatar-2-put-vody_avatar-the-way-of-water-2022-web-dl-2160p',
            'expected_title': 'Аватар',
            'expected_year': '2022',
            'has_imdb': True,
            'has_kp': True,
        },
    ],
)
async def test_real_torrent_info(torrent_data):
    """Test getting real torrent info (requires internet connection)"""
    # Skip if offline or in CI
    pytest.skip('Skipping external API test')

    try:
        message, _poster, _images, _, _ = await get_torrent_info(torrent_data['link'])

        # Check message content
        assert message is not None
        assert len(message) > 0

        # Check expected content
        if torrent_data.get('expected_title'):
            assert torrent_data['expected_title'] in message or '🎬' in message

        if torrent_data.get('expected_year'):
            assert torrent_data['expected_year'] in message

        if torrent_data.get('has_imdb'):
            assert 'IMDB:' in message or 'imdb.com' in message

        if torrent_data.get('has_kp'):
            assert 'Кинопоиск:' in message or 'kinopoisk.ru' in message

        # Technical details should be present
        assert '📀' in message

    except httpx.ConnectError:
        pytest.skip('Cannot connect to rutor.info')


@pytest.mark.integration
@pytest.mark.external
@pytest.mark.asyncio
@pytest.mark.parametrize(
    'rating_urls',
    [
        {
            'imdb': 'https://www.imdb.com/title/tt0133093/',  # The Matrix
            'kp': 'https://www.kinopoisk.ru/film/301/',
            'min_imdb_rating': 8.0,
            'min_kp_rating': 8.0,
        },
        {
            'imdb': 'https://www.imdb.com/title/tt0499549/',  # Avatar
            'kp': 'https://www.kinopoisk.ru/film/251733/',
            'min_imdb_rating': 7.0,
            'min_kp_rating': 7.0,
        },
    ],
)
async def test_real_movie_ratings(rating_urls):
    """Test getting real movie ratings (requires internet connection)"""
    # Skip if offline or in CI
    pytest.skip('Skipping external API test')

    try:
        imdb_rating, kp_rating = await get_movie_ratings(rating_urls.get('imdb'), rating_urls.get('kp'))

        # Check IMDB rating
        if rating_urls.get('imdb') and imdb_rating:
            rating_value = float(imdb_rating)
            assert rating_value >= rating_urls.get('min_imdb_rating', 0)
            assert rating_value <= 10.0

        # Check Kinopoisk rating
        if rating_urls.get('kp') and kp_rating:
            rating_value = float(kp_rating)
            assert rating_value >= rating_urls.get('min_kp_rating', 0)
            assert rating_value <= 10.0

    except httpx.ConnectError, httpx.TimeoutException:
        pytest.skip('Cannot connect to rating websites')
    except ValueError:
        # Rating format might have changed
        pytest.skip('Rating format parsing failed')
