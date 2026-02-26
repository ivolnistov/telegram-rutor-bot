from bs4 import BeautifulSoup

from telegram_rutor_bot.rutor.parser import _extract_movie_links, _extract_torrent_data


def test_extract_torrent_data_full():
    html = """
    <tr>
        <td>01&nbsp;Янв&nbsp;24</td>
        <td>
            <a href="/torrent/123">The Matrix (1999)</a>
            <a href="magnet:?xt=urn:btih:abc">M</a>
        </td>
        <td>1.5 GB</td>
        <td>10</td>
        <td>5</td>
    </tr>
    """
    soup = BeautifulSoup(html, 'html.parser')
    # lnk must be the magnet link
    lnk = soup.find_all('a', href=lambda h: h and h.startswith('magnet'))[0]

    data = _extract_torrent_data(lnk)
    assert data is not None
    assert data['name'] == 'The Matrix'
    assert data['year'] == 1999


def test_extract_movie_links_extended():
    html = """
    <div>
        <a href="https://www.imdb.com/title/tt0133093/">IMDB</a>
        <a href="https://www.kinopoisk.ru/film/123/">KP</a>
    </div>
    """
    soup = BeautifulSoup(html, 'html.parser')
    imdb, kp = _extract_movie_links(soup)
    assert 'tt0133093' in imdb
    assert '123' in kp
