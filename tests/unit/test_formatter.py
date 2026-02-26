from bs4 import BeautifulSoup
from telegram_rutor_bot.rutor.formatter import (
    _format_title_section,
    _format_ratings_section,
    _format_movie_details,
    _format_technical_details,
    _format_description_section,
    format_torrent_message
)

def test_format_title_section():
    soup = BeautifulSoup("<title>Test :: Rutor</title>", "lxml")
    
    # Test with explicit title
    res = _format_title_section({"title": "Matrix", "year": 1999}, soup)
    assert "🎬 Matrix (1999)" in res[0]
    
    # Test with original title
    res2 = _format_title_section({"title": "Matrix", "original_title": "The Matrix"}, soup)
    assert "🌍 The Matrix" in res2[1]
    
    # Test extraction from soup
    res3 = _format_title_section({}, soup)
    assert "🎬 Test" in res3[0]

def test_format_ratings_section():
    assert _format_ratings_section("8.5", "8.0") == ["⭐ IMDB: 8.5/10 | ⭐ Кинопоиск: 8.0/10"]
    assert _format_ratings_section("8.5", None) == ["⭐ IMDB: 8.5/10"]
    assert _format_ratings_section(None, None) == []

def test_format_movie_details():
    data = {
        "genre": "Action",
        "country": "USA",
        "duration": "02:00",
        "director": "Wachowski",
        "actors": "Keanu Reeves"
    }
    res = _format_movie_details(data)
    assert "📁 Жанр: Action" in res
    assert "👥 В ролях: Keanu Reeves" in res

def test_format_technical_details():
    data = {
        "quality": "1080p",
        "audio": ["Russian", "English"],
        "subtitles": "Russian"
    }
    res = _format_technical_details(data)
    assert "💎 Качество: 1080p" in res
    assert "🎙 Аудио 1: Russian" in res
    assert "🎙 Аудио 2: English" in res

def test_format_description_section():
    data = {"description": "Long plot..."}
    res = _format_description_section(data)
    assert "📝 Описание:" in res
    assert "Long plot..." in res

def test_format_torrent_message_full():
    soup = BeautifulSoup("<title>Page</title>", "lxml")
    data = {
        "title": "Inception",
        "quality": "BDRip",
        "imdb_url": "http://imdb.com/1"
    }
    msg = format_torrent_message(data, soup, "8.8", None, "/torrent/123/inception")
    assert "🎬 Inception" in msg
    assert "⭐ IMDB: 8.8/10" in msg
    assert "/dl_123" in msg
    assert "🔗 Rutor: https://www.rutor.info/torrent/123/inception" in msg
