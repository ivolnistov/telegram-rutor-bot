"""qBittorrent torrent client implementation"""

import asyncio
import contextlib
import json
from typing import Any, TypedDict, Unpack

import httpx

from .base import TorrentClient, TorrentClientError


class RequestKwargs(TypedDict, total=False):
    """Type for request kwargs"""

    data: dict[str, str]
    params: dict[str, str]


class QBittorrentClient(TorrentClient):
    """qBittorrent client implementation using httpx"""

    def __init__(self, host: str, port: int, username: str | None = None, password: str | None = None):
        self.base_url = f'http://{host}:{port}'
        self.api_url = f'{self.base_url}/api/v2'
        self.username = username
        self.password = password
        self._client: httpx.AsyncClient | None = None
        self._authenticated = False

    async def connect(self) -> None:
        """Connect to qBittorrent and authenticate"""
        self._client = httpx.AsyncClient()

        # Check if auth is bypassed (e.g. via IP Whitelist)
        try:
            check_resp = await self._client.get(f'{self.api_url}/app/version')
            if check_resp.status_code == 200:
                self._authenticated = True
                return
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        # Authenticate if credentials provided
        if self.username and self.password:
            response = await self._client.post(
                f'{self.api_url}/auth/login', data={'username': self.username, 'password': self.password}
            )

            if response.status_code != 200 or response.text != 'Ok.':
                raise TorrentClientError(f'qBittorrent authentication failed: {response.text}')

            # Get and store the cookie
            self._client.cookies = response.cookies
            self._authenticated = True

    async def disconnect(self) -> None:
        """Logout and close the HTTP client"""
        if self._client:
            if self._authenticated:
                with contextlib.suppress(Exception):
                    await self._client.post(f'{self.api_url}/auth/logout')
            await self._client.aclose()
            self._client = None
            self._authenticated = False

    async def _request(
        self, method: str, endpoint: str, **kwargs: Unpack[RequestKwargs]
    ) -> str | list[dict[str, Any]] | dict[str, Any]:
        """Make a request to qBittorrent API"""
        if not self._client:
            await self.connect()

        assert self._client is not None  # Ensured by connect()

        url = f'{self.api_url}/{endpoint}'
        response = await self._client.request(method, url, **kwargs)

        if response.status_code == 403:
            # Try to re-authenticate
            await self.connect()
            assert self._client is not None  # Ensured by connect()
            response = await self._client.request(method, url, **kwargs)

        response.raise_for_status()

        # Return JSON if content type is JSON
        if 'application/json' in response.headers.get('content-type', ''):
            result = response.json()
            # Type narrowing - we know the API returns either list or dict
            if isinstance(result, list | dict):
                return result
            # Fallback for unexpected response
            return str(result)
        return response.text

    async def add_torrent(
        self,
        magnet_link: str,
        download_dir: str | None = None,
        category: str | None = None,
        rename: str | None = None,
        ratio_limit: float | None = None,
        seed_time_limit: int | None = None,
        inactive_seeding_time_limit: int | None = None,
        tags: str | None = None,
    ) -> dict[str, Any]:
        """Add a torrent by magnet link"""
        data = {'urls': magnet_link}
        if download_dir:
            data['savepath'] = download_dir
        if category:
            data['category'] = category
        if ratio_limit is not None and ratio_limit > 0:
            data['ratioLimit'] = str(ratio_limit)
        if seed_time_limit is not None and seed_time_limit > 0:
            data['seedingTimeLimit'] = str(seed_time_limit)
        if inactive_seeding_time_limit is not None and inactive_seeding_time_limit > 0:
            # Note: Parameter name might be case sensitive or specific.
            # qBittorrent API usually uses camelCase: inactiveSeedingTimeLimit
            data['inactiveSeedingTimeLimit'] = str(inactive_seeding_time_limit)
        if rename:
            data['rename'] = rename
        if tags:
            data['tags'] = tags

        await self._request('POST', 'torrents/add', data=data)

        # qBittorrent doesn't return torrent info on add, so we need to find it
        # Wait a bit for the torrent to be added
        await asyncio.sleep(1)

        # Get all torrents and find the one we just added
        torrents = await self.list_torrents()
        for torrent in torrents:
            if magnet_link.lower() in torrent.get('magnet_uri', '').lower():
                return torrent

        # If not found by magnet, return a basic response
        return {
            'id': 'unknown',
            'name': 'Added torrent',
            'hash': 'unknown',
        }

    async def get_torrent(self, torrent_id: str | int) -> dict[str, Any] | None:
        """Get information about a specific torrent"""
        # In qBittorrent, torrent_id is the hash
        result = await self._request('GET', 'torrents/info', params={'hashes': str(torrent_id)})

        # torrents/info returns a list
        if isinstance(result, list) and len(result) > 0:
            torrent = result[0]
            return self._normalize_torrent_info(torrent)

        return None

    async def list_torrents(self) -> list[dict[str, Any]]:
        """List all torrents"""
        result = await self._request('GET', 'torrents/info')

        torrents: list[dict[str, Any]] = []
        if isinstance(result, list):
            for torrent in result:
                if isinstance(torrent, dict):
                    torrents.append(self._normalize_torrent_info(torrent))

        return torrents

    async def remove_torrent(self, torrent_id: str | int, delete_files: bool = False) -> bool:
        """Remove a torrent"""
        await self._request(
            'POST', 'torrents/delete', data={'hashes': str(torrent_id), 'deleteFiles': str(delete_files).lower()}
        )
        return True

    async def pause_torrent(self, torrent_id: str | int) -> bool:
        """Pause a torrent"""
        await self._request('POST', 'torrents/pause', data={'hashes': str(torrent_id)})
        return True

    async def resume_torrent(self, torrent_id: str | int) -> bool:
        """Resume a torrent"""
        await self._request('POST', 'torrents/resume', data={'hashes': str(torrent_id)})
        return True

    async def get_app_preferences(self) -> dict[str, Any]:
        """Get application preferences"""
        result = await self._request('GET', 'app/preferences')
        if isinstance(result, dict):
            return result
        raise TorrentClientError(f'Expected dict from app/preferences, got {type(result)}')

    async def set_app_preferences(self, prefs: dict[str, Any]) -> None:
        """Set application preferences"""
        # qBittorrent expects 'json' parameter containing the preferences
        # Note: keys must be exact match to qB API
        await self._request('POST', 'app/setPreferences', data={'json': json.dumps(prefs)})

    def _normalize_torrent_info(self, torrent: dict[str, Any]) -> dict[str, Any]:
        """Normalize qBittorrent torrent info to standard format"""
        return {
            'id': torrent.get('hash'),
            'name': torrent.get('name'),
            'hash': torrent.get('hash'),
            'size': torrent.get('size', 0),
            'progress': torrent.get('progress', 0) * 100,
            'status': torrent.get('state', 'unknown').lower(),
            'download_rate': torrent.get('dlspeed', 0),
            'upload_rate': torrent.get('upspeed', 0),
            'download_dir': torrent.get('save_path'),
            'magnet_uri': torrent.get('magnet_uri', ''),
            'seeds': torrent.get('num_seeds', 0),
            'peers': torrent.get('num_leechs', 0),
        }
