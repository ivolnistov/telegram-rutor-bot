from bs4 import BeautifulSoup
from telegram_rutor_bot.rutor.rating_parser import _extract_imdb_poster_src, _find_poster_element
from telegram_rutor_bot.rutor.constants import IMDB_V1_TOKEN, IMDB_V1_POSTER_REPLACE

def test_find_poster_element():
    html = '<html><body><img class="ipc-image" src="test.jpg"></body></html>'
    soup = BeautifulSoup(html, 'lxml')
    assert _find_poster_element(soup) is not None
    assert _find_poster_element(soup).name == 'img'

def test_extract_imdb_poster_src():
    # Test normal src
    html = '<html><body><img class="ipc-image" src="https://example.com/poster.jpg"></body></html>'
    soup = BeautifulSoup(html, 'lxml')
    assert _extract_imdb_poster_src(soup) == "https://example.com/poster.jpg"

    # Test IMDB V1 token replacement
    token = IMDB_V1_TOKEN
    replace = IMDB_V1_POSTER_REPLACE
    html_v1 = f'<html><body><img class="ipc-image" src="https://example.com/p{token}other.jpg"></body></html>'
    soup_v1 = BeautifulSoup(html_v1, 'lxml')
    expected = f"https://example.com/p{replace}"
    assert _extract_imdb_poster_src(soup_v1) == expected

def test_constants():
    from telegram_rutor_bot.rutor import constants
    assert constants.RUTOR_BASE_URL.startswith('https')
    assert constants.IMDB_V1_TOKEN == '._V1_'
