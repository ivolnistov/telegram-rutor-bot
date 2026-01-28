import pytest

from telegram_rutor_bot.api.routes.discovery import get_library
from telegram_rutor_bot.db.models import Film, User


@pytest.mark.asyncio
async def test_get_library_vote_average_logic(async_session):
    # 1. Setup Data
    # Film with both ratings
    film_both = Film(
        name='Both Ratings', kp_rating=8.5, rating=7.0, tmdb_media_type='movie', tmdb_id=1, blake='hash1', year=2023
    )
    # Film with only Rutor/TMDB rating
    film_rating_only = Film(
        name='Rating Only', kp_rating=None, rating=6.5, tmdb_media_type='movie', tmdb_id=2, blake='hash2', year=2023
    )
    # Film with only KP rating
    film_kp_only = Film(
        name='KP Only', kp_rating=7.8, rating=None, tmdb_media_type='movie', tmdb_id=3, blake='hash3', year=2023
    )
    # Film with no rating
    film_none = Film(
        name='No Rating', kp_rating=None, rating=None, tmdb_media_type='movie', tmdb_id=4, blake='hash4', year=2023
    )

    async_session.add_all([film_both, film_rating_only, film_kp_only, film_none])
    await async_session.commit()

    # Mock user
    user = User(id=1, chat_id=123, username='test')

    # 2. Call get_library
    results = await get_library(media_type='movie', limit=10, offset=0, user=user, db=async_session)

    # 3. Verify
    # Results are ordered by ID desc by default in get_library
    # id 4 (No Rating) -> id 3 (KP Only) -> id 2 (Rating Only) -> id 1 (Both)

    res_map = {r['title']: r for r in results}

    # Case 1: Both -> Should use KP (8.5)
    assert res_map['Both Ratings']['vote_average'] == 8.5
    assert res_map['Both Ratings']['kp_rating'] == 8.5

    # Case 2: Rating Only -> Should use Rating (6.5)
    assert res_map['Rating Only']['vote_average'] == 6.5
    assert res_map['Rating Only']['kp_rating'] is None

    # Case 3: KP Only -> Should use KP (7.8)
    assert res_map['KP Only']['vote_average'] == 7.8
    assert res_map['KP Only']['kp_rating'] == 7.8

    # Case 4: None -> Should allow 0.0 or None, code says 0.0
    assert res_map['No Rating']['vote_average'] == 0.0
    assert res_map['No Rating']['kp_rating'] is None
