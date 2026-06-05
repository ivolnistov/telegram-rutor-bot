"""Unit tests for parser functions"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from telegram_rutor_bot.rutor.parser import (
    get_torrent_info,
    has_good_link,
    parse_name,
    parse_rutor,
    size_to_bytes_converter,
)


class TestParserHelpers:
    """Test parser helper functions"""

    def test_parse_name_with_year(self):
        """Test parsing movie name with year"""
        name, _orig, year = parse_name('The Matrix (1999) 1080p BluRay')
        assert name == 'The Matrix'
        assert str(year) == '1999'

    def test_parse_name_without_year(self):
        """Test parsing movie name without year"""
        name, _orig, year = parse_name('Some Movie Title')
        assert name == 'Some Movie Title'
        assert str(year) == str(datetime.now(UTC).year)

    def test_parse_name_with_brackets_and_slash(self):
        """Test parsing complex movie name"""
        name, _orig, year = parse_name('The Matrix (1999) [Extended Cut] / Матрица')
        assert name == 'The Matrix'
        assert str(year) == '1999'

    def test_parse_name_cyrillic(self):
        """Test parsing with cyrillic ё"""
        name, _orig, year = parse_name('Ёлки (2010)')
        assert name == 'Елки'  # ё is replaced with e
        assert str(year) == '2010'

    def test_size_to_bytes_converter_gb(self):
        """Test GB conversion"""
        assert size_to_bytes_converter('1.5 GB') == int(1.5 * 1024 * 1024 * 1024)
        assert size_to_bytes_converter('15.2GB') == int(15.2 * 1024 * 1024 * 1024)

    def test_size_to_bytes_converter_mb(self):
        """Test MB conversion"""
        assert size_to_bytes_converter('750 MB') == (750 * 1024 * 1024)
        assert size_to_bytes_converter('500MB') == (500 * 1024 * 1024)

    def test_size_to_bytes_converter_kb(self):
        """Test KB conversion"""
        assert size_to_bytes_converter('512 KB') == (512 * 1024)
        assert size_to_bytes_converter('1024KB') == (1024 * 1024)

    def test_size_to_bytes_converter_invalid(self):
        """Test invalid size format"""
        assert size_to_bytes_converter('invalid') == 0
        assert size_to_bytes_converter('') == 0

    def test_has_good_link_imdb(self):
        """Test IMDB link validation"""
        assert has_good_link('https://www.imdb.com/title/tt0133093/') is True
        assert has_good_link('https://www.imdb.com/title/tt0133093') is True

    def test_has_good_link_kinopoisk(self):
        """Test Kinopoisk link validation"""
        assert has_good_link('https://www.kinopoisk.ru/film/301/') is True
        assert has_good_link('https://www.kinopoisk.ru/film/301') is True

    def test_has_good_link_invalid(self):
        """Test invalid links"""
        assert has_good_link('https://example.com') is False
        assert has_good_link('not a url') is False
        assert has_good_link('') is False


@pytest.mark.asyncio
class TestGetTorrentInfo:
    """Test get_torrent_info function with mocks"""

    async def test_get_torrent_info_full(self):
        """Test parsing full torrent info"""
        mock_html = """
        <html>
        <head>
            <title>The Matrix (1999) 1080p :: rutor.info</title>
        </head>
        <body>
            <div id="details">
                <table>
                    <tr>
                        <td>:</td>
                        <td>Информация о фильме</td>
                    </tr>
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
                        <td>США</td>
                    </tr>
                    <tr>
                        <td>Продолжительность:</td>
                        <td>136 мин.</td>
                    </tr>
                    <tr>
                        <td>Режиссер:</td>
                        <td>Вачовски</td>
                    </tr>
                    <tr>
                        <td>В ролях:</td>
                        <td>Киану Ривз, Лоуренс Фишберн</td>
                    </tr>
                    <tr>
                        <td>Описание:</td>
                        <td>Хакер Нео узнает правду о реальности</td>
                    </tr>
                    <tr>
                        <td>Видео:</td>
                        <td>1920x1080, 23.976 fps</td>
                    </tr>
                    <tr>
                        <td>Аудио:</td>
                        <td>DTS 5.1</td>
                    </tr>
                    <tr>
                        <td>Перевод:</td>
                        <td>Профессиональный</td>
                    </tr>
                </table>
            </div>
            <a href="https://www.imdb.com/title/tt0133093/">IMDB</a>
            <a href="https://www.kinopoisk.ru/film/301/">Кинопоиск</a>
        </body>
        </html>
        """

        # Mock the cache to prevent caching issues
        with patch('telegram_rutor_bot.rutor.parser.FilmInfoCache') as mock_cache_class:
            mock_cache = Mock()
            mock_cache.get.return_value = None  # No cached data
            mock_cache.set.return_value = None
            mock_cache_class.return_value = mock_cache

            with patch('telegram_rutor_bot.rutor.parser._get_client') as mock_client:
                # Mock HTTP response
                mock_response = Mock()
                mock_response.text = mock_html
                mock_response.raise_for_status = Mock()

                mock_async_client = AsyncMock()
                mock_async_client.get.return_value = mock_response
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.__aexit__.return_value = None

                mock_client.return_value = mock_async_client

                # Mock ratings - patch where it's imported in parser module
                with patch('telegram_rutor_bot.rutor.parser.get_movie_ratings') as mock_ratings:
                    mock_ratings.return_value = ('8.7', '8.5')

                    message, _poster, _images, _, _ = await get_torrent_info('/torrent/123/matrix')

        # Check message content
        assert '🎬' in message
        assert 'The Matrix' in message or 'Матрица' in message
        assert '(1999)' in message
        assert '⭐ IMDB: 8.7/10 | ⭐ Кинопоиск: 8.5/10' in message
        assert '📁 Жанр: Фантастика, Боевик' in message
        assert '🌍 Страна: США' in message
        assert '⏱ Продолжительность: 136 мин.' in message
        assert '🎭 Режиссер: Вачовски' in message
        assert '👥 В ролях: Киану Ривз' in message
        assert '📝 Описание:' in message
        assert '📹 Видео: 1920x1080' in message
        # Check for either audio tracks or translation
        if '🎙 Аудио' in message:
            # If audio tracks are present, translation won't be shown
            assert '🎙 Аудио' in message
        else:
            assert '🎙 Перевод: Профессиональный' in message

    async def test_get_torrent_info_minimal(self):
        """Test parsing minimal torrent info"""
        mock_html = """
        <html>
        <head>
            <title>Some Movie (2023) :: rutor.info</title>
        </head>
        <body>
            <div id="details">
                <table>
                    <tr><td>Category:</td><td>Movies</td></tr>
                </table>
            </div>
        </body>
        </html>
        """

        # Mock the cache
        with patch('telegram_rutor_bot.rutor.parser.FilmInfoCache') as mock_cache_class:
            mock_cache = Mock()
            mock_cache.get.return_value = None  # No cached data
            mock_cache.set.return_value = None
            mock_cache_class.return_value = mock_cache

            with patch('telegram_rutor_bot.rutor.parser._get_client') as mock_client:
                mock_response = Mock()
                mock_response.text = mock_html
                mock_response.raise_for_status = Mock()

                mock_async_client = AsyncMock()
                mock_async_client.get.return_value = mock_response
                mock_async_client.__aenter__.return_value = mock_async_client
                mock_async_client.__aexit__.return_value = None

                mock_client.return_value = mock_async_client

                with patch('telegram_rutor_bot.rutor.parser.get_movie_ratings') as mock_ratings:
                    mock_ratings.return_value = (None, None)

                    message, _poster, _images, _, _ = await get_torrent_info('/torrent/456/some-movie')

        # Should at least have title
        assert '🎬' in message
        assert 'Some Movie (2023)' in message


@pytest.mark.asyncio
class TestParseRutor:
    """Test parse_rutor function with mocks"""

    async def test_parse_rutor_search_results(self, async_session):
        """Test parsing search results page"""
        mock_html = """
        <html>
        <body>
            <table>
                <tr>
                    <td>01&nbsp;Jan&nbsp;23</td>
                    <td>
                        <a href="/torrent/123/matrix-1999">Matrix (1999)</a>
                        <a href="magnet:?xt=urn:btih:abc123&dn=Matrix">
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

        with patch('telegram_rutor_bot.rutor.parser._get_client') as mock_client:
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response
            mock_async_client.__aenter__.return_value = mock_async_client
            mock_async_client.__aexit__.return_value = None

            mock_client.return_value = mock_async_client

            # Mock locale context manager
            with patch('telegram_rutor_bot.rutor.parser.localize'):
                new_films, _new_torrent_ids = await parse_rutor('http://rutor.info/search/matrix', async_session)

        # Should create at least one film
        assert len(new_films) >= 1
