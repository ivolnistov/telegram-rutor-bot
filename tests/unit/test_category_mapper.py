import pytest
from telegram_rutor_bot.utils.category_mapper import map_genre_to_category, detect_category_from_title, map_rutor_category

def test_map_genre_to_category():
    assert map_genre_to_category(None) is None
    assert map_genre_to_category("боевик") == "FILMS"
    assert map_genre_to_category("комедия") == "FILMS"
    # Testing some that should map to TVSHOWS if keywords are in settings
    # But settings are mocked/loaded from config. Here we just test the logic.

def test_detect_category_from_title():
    assert detect_category_from_title(None) is None
    assert detect_category_from_title("The Matrix 1999") == "FILMS"
    assert detect_category_from_title("S01E01") == "TVSHOWS"
    assert detect_category_from_title("1-10 серия") == "TVSHOWS"

def test_map_rutor_category():
    assert map_rutor_category(None) is None
    assert map_rutor_category("Зарубежные фильмы") == "FILMS"
    assert map_rutor_category("Зарубежные сериалы") == "TVSHOWS"
    assert map_rutor_category("Мультфильмы") == "CARTOONS"
    assert map_rutor_category("Неизвестно") == "FILMS" # Fallback
