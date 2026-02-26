from telegram_rutor_bot.utils.markdown import escape_markdown


def test_markdown_full_coverage():
    # escape_markdown empty
    assert escape_markdown('') == ''
    assert escape_markdown(None) is None

    # escape_markdown characters
    assert escape_markdown('test*') == r'test\*'
