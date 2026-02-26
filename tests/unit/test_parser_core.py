from bs4 import BeautifulSoup

from telegram_rutor_bot.rutor.parser import (
    _extract_details_from_table,
    _extract_movie_info_from_blocks,
    _parse_torrent_page_details,
)


def test_extract_details_from_table_minimal():
    # Must have id="details"
    html = """
    <div id="details">
        <table>
            <tr><td><b>Качество:</b></td><td>BDRip 1080p</td></tr>
            <tr><td><b>Видео:</b></td><td>MPEG-4 AVC</td></tr>
        </table>
    </div>
    """
    soup = BeautifulSoup(html, 'lxml')
    res = _extract_details_from_table(soup)
    assert res['quality'] == 'BDRip 1080p'
    assert res['video_quality'] == 'MPEG-4 AVC'


def test_extract_movie_info_from_blocks():
    # Must contain "Информация о фильме" and newlines
    # The keys in parser.py are exact: 'Год выпуска', 'Страна', 'Жанр'
    html = """
    <table>
        <tr>
            <td>
                Информация о фильме\n
                Год выпуска: 2024\n
                Страна: США\n
                Жанр: Боевик\n
            </td>
        </tr>
    </table>
    """
    soup = BeautifulSoup(html, 'lxml')
    res = _extract_movie_info_from_blocks(soup)
    assert res['year'] == '2024'
    assert res['country'] == 'США'
    assert res['genre'] == 'Боевик'


def test_parse_torrent_page_details_mock():
    html = """
    <html>
        <title>The Matrix :: Rutor</title>
        <body>
            <div id="details">
                <a href="https://www.imdb.com/title/tt0133093/">IMDB</a>
                <table>
                    <tr><td>Качество:</td><td>1080p</td></tr>
                </table>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'lxml')
    imdb, kp, res = _parse_torrent_page_details(soup)
    assert imdb == 'https://www.imdb.com/title/tt0133093/'
    assert res['quality'] == '1080p'
