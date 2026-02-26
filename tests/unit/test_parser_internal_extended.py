from telegram_rutor_bot.rutor.parser import _extract_description, _parse_genre_from_lines, _process_field


def test_parse_genre_from_lines():
    assert _parse_genre_from_lines(['Жанр: Action', 'Year: 2020']) == 'Action'
    assert _parse_genre_from_lines(['Nothing', 'No genre here']) is None


def test_extract_genre_from_movie_block():
    pass


def test_extract_description_extended():
    lines = ['Header', '---', 'The Story of a man...', 'End of story', 'DVD Info:']
    # Based on grep: it breaks if line ends with ':'
    assert 'The Story' in _extract_description(lines, 2)
    assert 'DVD Info' not in _extract_description(lines, 2)


def test_process_field_actors():
    res = {}
    _process_field('В ролях', 'Actor 1, Actor 2', res)
    assert res['actors'] == 'Actor 1, Actor 2'


def test_process_field_country():
    res = {}
    _process_field('Страна', 'USA, UK', res)
    assert res['country'] == 'USA, UK'
