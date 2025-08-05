"""Unit tests for torrent client abstractions"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from telegram_rutor_bot.torrent_clients import get_torrent_client
from telegram_rutor_bot.torrent_clients.base import TorrentClientError
from telegram_rutor_bot.torrent_clients.qbittorrent import QBittorrentClient
from telegram_rutor_bot.torrent_clients.transmission import TransmissionClient


class TestTorrentClientFactory:
    """Test torrent client factory function"""

    def test_get_transmission_client(self, test_settings):
        """Test getting Transmission client"""
        test_settings.torrent_client = 'transmission'

        # Patch the import where it's used, not where it's defined
        with patch('telegram_rutor_bot.torrent_clients.factory.settings', test_settings):
            client = get_torrent_client()

        assert isinstance(client, TransmissionClient)
        assert (
            client.url == f'http://{test_settings.transmission_host}:{test_settings.transmission_port}/transmission/rpc'
        )

    def test_get_qbittorrent_client(self, test_settings):
        """Test getting qBittorrent client"""
        test_settings.torrent_client = 'qbittorrent'

        with patch('telegram_rutor_bot.torrent_clients.factory.settings', test_settings):
            client = get_torrent_client()

        assert isinstance(client, QBittorrentClient)
        assert client.api_url == f'http://{test_settings.qbittorrent_host}:{test_settings.qbittorrent_port}/api/v2'

    def test_invalid_client_raises_error(self, test_settings):
        """Test that invalid client name raises error"""
        test_settings.torrent_client = 'invalid'

        with (
            patch('telegram_rutor_bot.torrent_clients.factory.settings', test_settings),
            pytest.raises(ValueError, match='Unknown torrent client'),
        ):
            get_torrent_client()


class TestTransmissionClient:
    """Test Transmission client implementation"""

    @pytest.fixture
    def transmission_client(self, test_settings):
        """Create Transmission client instance"""
        return TransmissionClient(
            host=test_settings.transmission_host,
            port=test_settings.transmission_port,
            username=test_settings.transmission_username,
            password=test_settings.transmission_password,
        )

    @pytest.mark.asyncio
    async def test_connect_success(self, transmission_client):
        """Test successful connection"""
        # Mock the httpx client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.headers = {'X-Transmission-Session-Id': 'test-session-id'}
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient', return_value=mock_client):
            await transmission_client.connect()

            assert transmission_client._session_id == 'test-session-id'
            assert transmission_client._client is not None

    @pytest.mark.asyncio
    async def test_connect_no_session_id(self, transmission_client):
        """Test connection failure when no session ID returned"""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.headers = {}
        mock_client.post = AsyncMock(return_value=mock_response)

        with (
            patch('httpx.AsyncClient', return_value=mock_client),
            pytest.raises(TorrentClientError, match='Failed to get Transmission session ID'),
        ):
            await transmission_client.connect()

    @pytest.mark.asyncio
    async def test_add_torrent(self, transmission_client):
        """Test adding a torrent"""
        magnet_link = 'magnet:?xt=urn:btih:1234567890abcdef'

        # Setup mock client with session ID
        transmission_client._client = AsyncMock()
        transmission_client._session_id = 'test-session-id'

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': 'success', 'arguments': {'torrent-added': {'id': 1}}}
        mock_response.raise_for_status = Mock()
        transmission_client._client.post = AsyncMock(return_value=mock_response)

        result = await transmission_client.add_torrent(magnet_link)

        assert isinstance(result, dict)
        assert result['id'] == 1
        transmission_client._client.post.assert_called_once()
        call_args = transmission_client._client.post.call_args
        assert call_args[1]['json']['arguments']['filename'] == magnet_link

    @pytest.mark.asyncio
    async def test_list_torrents(self, transmission_client):
        """Test listing torrents"""
        # Setup mock client with session ID
        transmission_client._client = AsyncMock()
        transmission_client._session_id = 'test-session-id'

        mock_response = Mock()
        mock_response.json.return_value = {
            'result': 'success',
            'arguments': {
                'torrents': [{'id': 1, 'name': 'Torrent 1', 'status': 4}, {'id': 2, 'name': 'Torrent 2', 'status': 6}]
            },
        }
        mock_response.raise_for_status = Mock()
        transmission_client._client.post = AsyncMock(return_value=mock_response)

        torrents = await transmission_client.list_torrents()

        assert len(torrents) == 2
        assert torrents[0]['name'] == 'Torrent 1'
        assert torrents[1]['name'] == 'Torrent 2'


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
