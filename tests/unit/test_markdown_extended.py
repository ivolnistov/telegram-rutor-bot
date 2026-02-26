import pytest
from telegram_rutor_bot.utils.markdown import escape_markdown

def test_escape_markdown_basic():
    # Test characters that need escaping
    assert escape_markdown("test*") == r"test\*"
    assert escape_markdown("test_") == r"test\_"
    assert escape_markdown("test`") == r"test\`"
    assert escape_markdown("test[") == r"test\["
    
    # Test None
    assert escape_markdown(None) is None
