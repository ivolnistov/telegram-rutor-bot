"""Unit tests for torrent client abstractions"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from telegram_rutor_bot.torrent_clients import get_torrent_client
from telegram_rutor_bot.torrent_clients.qbittorrent import QBittorrentClient


class TestTorrentClientFactory:
    """Test torrent client factory function"""

    def test_get_qbittorrent_client(self, test_settings):
        """Test getting qBittorrent client"""
        # Even if 'torrent_client' setting exists or not, factory now always returns QBittorrent
        # But let's check basic instantiation
        with patch('telegram_rutor_bot.torrent_clients.factory.settings', test_settings):
            client = get_torrent_client()

        assert isinstance(client, QBittorrentClient)
        assert client.api_url == f'http://{test_settings.qbittorrent_host}:{test_settings.qbittorrent_port}/api/v2'


class TestQBittorrentClient:
    """Test qBittorrent client implementation"""

    @pytest.fixture
    def qbittorrent_client(self, test_settings):
        """Create qBittorrent client instance"""
        return QBittorrentClient(
            host=test_settings.qbittorrent_host,
            port=test_settings.qbittorrent_port,
            username=test_settings.qbittorrent_username,
            password=test_settings.qbittorrent_password,
        )

    @pytest.mark.asyncio
    async def test_connect_success(self, qbittorrent_client):
        """Test successful connection"""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'Ok.'
        mock_response.cookies = {}
        mock_response.raise_for_status = Mock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient', return_value=mock_client):
            await qbittorrent_client.connect()

            assert qbittorrent_client._client is not None
            mock_client.post.assert_called_with(
                f'{qbittorrent_client.api_url}/auth/login',
                data={'username': qbittorrent_client.username, 'password': qbittorrent_client.password},
            )

    @pytest.mark.asyncio
    async def test_add_torrent(self, qbittorrent_client):
        """Test adding a torrent"""
        magnet_link = 'magnet:?xt=urn:btih:1234567890abcdef'

        # Setup mock client
        qbittorrent_client._client = AsyncMock()

        # Mock responses for both add and list calls
        mock_add_response = Mock()
        mock_add_response.text = 'Ok.'
        mock_add_response.headers = {'content-type': 'text/plain'}
        mock_add_response.raise_for_status = Mock()

        mock_list_response = Mock()
        mock_list_response.json.return_value = []  # Empty list, no torrents found
        mock_list_response.headers = {'content-type': 'application/json'}
        mock_list_response.raise_for_status = Mock()

        # Mock to return different responses based on the request
        async def mock_request(method, url, **kwargs):
            if method == 'POST' and url.endswith('/torrents/add'):
                return mock_add_response
            if method == 'GET' and url.endswith('/torrents/info'):
                return mock_list_response
            return Mock()

        qbittorrent_client._client.request = AsyncMock(side_effect=mock_request)

        result = await qbittorrent_client.add_torrent(magnet_link)

        assert isinstance(result, dict)
        assert result['name'] == 'Added torrent'
        # Should make 2 calls: POST to add torrent, GET to list torrents
        assert qbittorrent_client._client.request.call_count == 2

        # Check first call (add torrent)
        add_call = qbittorrent_client._client.request.call_args_list[0]
        assert add_call[0][0] == 'POST'
        assert add_call[0][1].endswith('/torrents/add')
        assert add_call[1]['data']['urls'] == magnet_link

        # Check second call (list torrents)
        list_call = qbittorrent_client._client.request.call_args_list[1]
        assert list_call[0][0] == 'GET'
        assert list_call[0][1].endswith('/torrents/info')

    @pytest.mark.asyncio
    async def test_list_torrents(self, qbittorrent_client):
        """Test listing torrents"""
        # Setup mock client
        qbittorrent_client._client = AsyncMock()

        mock_response = Mock()
        mock_response.json.return_value = [
            {'hash': 'abc123', 'name': 'Torrent 1', 'state': 'downloading', 'progress': 0.5},
            {'hash': 'def456', 'name': 'Torrent 2', 'state': 'seeding', 'progress': 1.0},
        ]
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.raise_for_status = Mock()
        qbittorrent_client._client.request = AsyncMock(return_value=mock_response)

        torrents = await qbittorrent_client.list_torrents()

        assert len(torrents) == 2
        assert torrents[0]['name'] == 'Torrent 1'
        assert torrents[1]['name'] == 'Torrent 2'
