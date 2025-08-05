"""Transmission torrent client implementation"""

from typing import Any

import httpx

from .base import TorrentClient, TorrentClientError


class TransmissionClient(TorrentClient):
    """Transmission client implementation using httpx"""

    def __init__(self, host: str, port: int, username: str | None = None, password: str | None = None):
        self.url = f'http://{host}:{port}/transmission/rpc'
        self.auth = httpx.BasicAuth(username, password) if username and password else None
        self._session_id: str | None = None
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        """Connect to Transmission and get session ID"""
        self._client = httpx.AsyncClient(auth=self.auth)

        # Get session ID
        response = await self._client.post(self.url)
        self._session_id = response.headers.get('X-Transmission-Session-Id')

        if not self._session_id:
            raise TorrentClientError('Failed to get Transmission session ID')

    async def disconnect(self) -> None:
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._session_id = None

    async def _request(self, method: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a request to Transmission RPC"""
        if not self._client or not self._session_id:
            await self.connect()

        assert self._client is not None  # Ensured by connect()
        assert self._session_id is not None  # Ensured by connect()

        headers = {'X-Transmission-Session-Id': self._session_id}
        data = {'method': method, 'arguments': arguments or {}}

        response = await self._client.post(self.url, json=data, headers=headers)

        # Handle session ID renewal
        if response.status_code == 409:
            new_session_id = response.headers.get('X-Transmission-Session-Id')
            if new_session_id:
                self._session_id = new_session_id
                headers['X-Transmission-Session-Id'] = new_session_id
                response = await self._client.post(self.url, json=data, headers=headers)

        response.raise_for_status()
        result = response.json()

        if result.get('result') != 'success':
            raise TorrentClientError(f'Transmission error: {result.get("result", "Unknown error")}')

        arguments = result.get('arguments', {})
        return arguments if isinstance(arguments, dict) else {}

    async def add_torrent(
        self, magnet_link: str, download_dir: str | None = None, category: str | None = None
    ) -> dict[str, Any]:
        """Add a torrent by magnet link"""
        args = {'filename': magnet_link}
        if download_dir:
            args['download-dir'] = download_dir
        # Note: Transmission doesn't support categories natively
        # We could use labels in newer versions or custom download directories

        result = await self._request('torrent-add', args)

        # Return standardized torrent info
        torrent = result.get('torrent-added') or result.get('torrent-duplicate')
        if torrent:
            return {
                'id': torrent.get('id'),
                'name': torrent.get('name'),
                'hash': torrent.get('hashString'),
            }

        raise TorrentClientError('Failed to add torrent')

    async def get_torrent(self, torrent_id: str | int) -> dict[str, Any] | None:
        """Get information about a specific torrent"""
        result = await self._request(
            'torrent-get',
            {
                'ids': [int(torrent_id)],
                'fields': [
                    'id',
                    'name',
                    'status',
                    'hashString',
                    'totalSize',
                    'percentDone',
                    'rateDownload',
                    'rateUpload',
                    'downloadDir',
                    'files',
                    'trackers',
                    'peers',
                ],
            },
        )

        torrents = result.get('torrents', [])
        if torrents:
            torrent = torrents[0]
            return {
                'id': torrent.get('id'),
                'name': torrent.get('name'),
                'hash': torrent.get('hashString'),
                'size': torrent.get('totalSize'),
                'progress': torrent.get('percentDone', 0) * 100,
                'status': self._get_status_string(torrent.get('status')),
                'download_rate': torrent.get('rateDownload', 0),
                'upload_rate': torrent.get('rateUpload', 0),
                'download_dir': torrent.get('downloadDir'),
            }

        return None

    async def list_torrents(self) -> list[dict[str, Any]]:
        """List all torrents"""
        result = await self._request(
            'torrent-get',
            {
                'fields': [
                    'id',
                    'name',
                    'status',
                    'hashString',
                    'totalSize',
                    'percentDone',
                    'rateDownload',
                    'rateUpload',
                ]
            },
        )

        torrents = []
        for torrent in result.get('torrents', []):
            torrents.append(
                {
                    'id': torrent.get('id'),
                    'name': torrent.get('name'),
                    'hash': torrent.get('hashString'),
                    'size': torrent.get('totalSize'),
                    'progress': torrent.get('percentDone', 0) * 100,
                    'status': self._get_status_string(torrent.get('status')),
                    'download_rate': torrent.get('rateDownload', 0),
                    'upload_rate': torrent.get('rateUpload', 0),
                }
            )

        return torrents

    async def remove_torrent(self, torrent_id: str | int, delete_files: bool = False) -> bool:
        """Remove a torrent"""
        await self._request('torrent-remove', {'ids': [int(torrent_id)], 'delete-local-data': delete_files})
        return True

    async def pause_torrent(self, torrent_id: str | int) -> bool:
        """Pause a torrent"""
        await self._request('torrent-stop', {'ids': [int(torrent_id)]})
        return True

    async def resume_torrent(self, torrent_id: str | int) -> bool:
        """Resume a torrent"""
        await self._request('torrent-start', {'ids': [int(torrent_id)]})
        return True

    @staticmethod
    def _get_status_string(status: int) -> str:
        """Convert Transmission status code to string"""
        status_map = {
            0: 'stopped',
            1: 'check_wait',
            2: 'check',
            3: 'download_wait',
            4: 'download',
            5: 'seed_wait',
            6: 'seed',
        }
        return status_map.get(status, 'unknown')
