from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_rutor_bot.rutor.parser import parse_rutor


@pytest.mark.asyncio
async def test_parse_rutor_with_results(mocker):
    # Mock httpx response with a minimal Rutor table
    html = """
    <html>
    <body>
        <div id="index">
            <table>
                <tr class="g">
                    <td>01 Янв 24</td>
                    <td><a href="/torrent/123/name">Name</a></td>
                    <td><a href="magnet:?xt=urn:btih:abc">M</a></td>
                    <td>1.5 GB</td>
                    <td class="s">10</td>
                    <td class="p">5</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mocker.patch(
        'telegram_rutor_bot.rutor.parser._get_client',
        return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_client), __aexit__=AsyncMock()),
    )

    # Mock internal helpers
    mocker.patch(
        'telegram_rutor_bot.rutor.parser.localize', return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock())
    )
    mocker.patch('telegram_rutor_bot.rutor.parser._process_torrent_item', AsyncMock(return_value=1))

    res = await parse_rutor(AsyncMock(), 'http://test')
    assert isinstance(res, list)
