"""Real parser tests"""

import pytest

from telegram_rutor_bot.rutor.parser import get_torrent_info
from telegram_rutor_bot.rutor.rating_parser import get_movie_ratings


@pytest.mark.asyncio
async def test_parse_torrent_100():
    """Test parsing torrent ID 100 - The Unlit movie"""
    torrent_link = '/torrent/840427/mama-vozvrawenie-iz-tmy_the-unlit-2020-web-dl-1080p-itunes'

    message, poster, images = await get_torrent_info(torrent_link, '/dl_100')

    # Print for debugging
    print('\n' + '=' * 60)
    print('MESSAGE:')
    print(message)
    print('=' * 60)
    print(f'Has poster: {poster is not None}')
    print(f'Poster size: {len(poster) if poster else 0} bytes')
    print(f'Number of images: {len(images)}')

    # Assertions
    assert message is not None
    assert len(message) > 0

    # Should contain title from page
    assert 'Мама: Возвращение из тьмы' in message or 'The Unlit' in message or '🎬' in message

    # Should contain download link
    assert '/dl_100' in message

    # Should have some structure
    assert '📀' in message or '💾' in message


@pytest.mark.asyncio
async def test_get_ratings():
    """Test getting movie ratings from IMDB and Kinopoisk"""
    imdb_url = 'https://www.imdb.com/title/tt8115996/'  # The Unlit
    kp_url = 'https://www.kinopoisk.ru/film/1130869/'

    imdb_rating, kp_rating = await get_movie_ratings(imdb_url, kp_url)

    print(f'\nIMDB Rating: {imdb_rating}')
    print(f'Kinopoisk Rating: {kp_rating}')

    # At least one rating might be available
    # Don't assert specific values as they can change
    assert imdb_rating is not None or kp_rating is not None
