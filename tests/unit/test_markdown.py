from telegram_rutor_bot.utils.markdown import escape_markdown, escape_markdown_v2


def test_escape_markdown():
    text = 'Hello [World] *Asterisk* _Underscore_ `Code`'
    escaped = escape_markdown(text)
    assert r'\[' in escaped
    assert r'\*' in escaped
    assert r'\`' in escaped


def test_escape_markdown_v2():
    text = 'Hello #Hash'
    escaped = escape_markdown_v2(text)
    assert r'\#' in escaped
