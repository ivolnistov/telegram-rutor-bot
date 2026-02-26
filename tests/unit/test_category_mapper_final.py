from telegram_rutor_bot.utils.category_mapper import (
    detect_category_from_title,
    map_genre_to_category,
    map_rutor_category,
)


def test_mapper_edge_cases():
    # map_genre_to_category unknown
    assert map_genre_to_category('Nonexistent') == 'FILMS'

    # detect_category_from_title tvshows
    assert detect_category_from_title('Series Name S01E01') == 'TVSHOWS'
    assert detect_category_from_title('Movie Name 2024') == 'FILMS'

    # map_rutor_category
    assert map_rutor_category('Зарубежные сериалы') == 'TVSHOWS'
