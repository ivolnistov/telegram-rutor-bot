import pytest
from bs4 import BeautifulSoup
from unittest.mock import MagicMock, AsyncMock
from telegram_rutor_bot.rutor.parser import (
    _process_field,
    _process_movie_field,
    _extract_description,
    has_good_link,
    _extract_movie_links,
    _is_poster_image,
    parse_name,
    _determine_category,
    _should_skip_torrent
)

def test_parser_internal_helpers_v2():
    # _process_field
    res = {}
    _process_field("Описание", "Great movie", res)
    assert res["description"] == "Great movie"
    _process_field("В ролях", "Actor 1", res)
    assert res["actors"] == "Actor 1"
    
    # _process_movie_field
    res_m = {}
    _process_movie_field("Название", "Title", res_m)
    assert res_m["title"] == "Title"
    _process_movie_field("Аудио", "English", res_m)
    assert res_m["audio"] == ["English"]
    
    # _extract_description
    lines = ["О фильме:", "Desc line 1", "Desc line 2", "Another field:"]
    assert _extract_description(lines, 1) == "Desc line 1 Desc line 2"
    
    # has_good_link (MUST use www as per parser.py RE)
    assert has_good_link("http://www.imdb.com/title/tt123") is True
    assert has_good_link("http://www.kinopoisk.ru/film/123") is True
    assert has_good_link("http://rutor.info") is False
    
    # _extract_movie_links
    soup = BeautifulSoup('<a href="http://www.imdb.com/title/tt1"></a><a href="http://www.kinopoisk.ru/film/2"></a>', 'lxml')
    imdb, kp = _extract_movie_links(soup)
    assert "tt1" in imdb
    assert "2" in kp
    
    # _is_poster_image
    assert _is_poster_image("poster.jpg", b"data", 0) is True
    assert _is_poster_image("screen.jpg", b"data" * 100000, 0) is True
    assert _is_poster_image("screen.jpg", b"data", 5) is False
    
    # parse_name
    name, original_name, year = parse_name("Movie / Original (2024) [1080p]")
    assert name == "Movie"
    assert original_name == "Original"
    assert year == 2024
    
    # _determine_category
    assert _determine_category(None, "Сериалы", "Show") == 'TVSHOWS'
    assert _determine_category(None, "Зарубежные фильмы", "Movie") == 'FILMS'
    
    # _should_skip_torrent
    assert _should_skip_torrent("CAMRip movie", []) is True
    assert _should_skip_torrent("Proper Bluray", []) is False
