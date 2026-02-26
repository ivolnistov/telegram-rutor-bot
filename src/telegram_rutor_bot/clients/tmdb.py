import urllib.parse
from typing import Any, cast

import httpx

from telegram_rutor_bot.config import settings


class TmdbClient:
    """Client for The Movie Database API (v3)"""

    BASE_URL = 'https://api.themoviedb.org/3'

    def __init__(self) -> None:
        """Initialize TmdbClient with global config"""
        pass

    @property
    def api_key(self) -> str | None:
        return settings.tmdb_api_key

    @property
    def language(self) -> str:
        return settings.tmdb_language or 'ru-RU'

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.api_key:
            return {}

        if params is None:
            params = {}

        params['api_key'] = self.api_key
        params['language'] = self.language

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Validate endpoint to prevent unintended path traversal
                safe_endpoint = urllib.parse.quote(endpoint, safe='/_')
                response = await client.get(f'{self.BASE_URL}{safe_endpoint}', params=params)
                response.raise_for_status()
                return cast(dict[str, Any], response.json())

            except httpx.HTTPError:
                return {}

    async def create_request_token(self) -> str | None:
        """Create a temporary request token."""
        data = await self._get('/authentication/token/new')
        return cast(str | None, data.get('request_token'))

    async def create_session_id(self, request_token: str) -> str | None:
        """Create a session ID from an authorized request token."""
        if not self.api_key:
            return None

        params = {'api_key': self.api_key}
        payload = {'request_token': request_token}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(f'{self.BASE_URL}/authentication/session/new', params=params, json=payload)
                response.raise_for_status()
                return cast(str | None, response.json().get('session_id'))
            except httpx.HTTPError:
                return None

    async def get_trending(self, media_type: str = 'all', time_window: str = 'week') -> list[dict[str, Any]]:
        """
        Get trending items.

        :param media_type: all, movie, tv, person
        :param time_window: day, week
        """
        data = await self._get(f'/trending/{media_type}/{time_window}')
        return cast(list[dict[str, Any]], data.get('results', []))

    async def search_multi(self, query: str) -> list[dict[str, Any]]:
        """Search for movies, TV shows and people."""
        if not query:
            return []
        data = await self._get('/search/multi', params={'query': query})
        return cast(list[dict[str, Any]], data.get('results', []))

    async def get_details(
        self, media_type: str, media_id: int, append_to_response: str | None = None
    ) -> dict[str, Any]:
        """Get details for a movie or TV show."""
        params = {}
        if append_to_response:
            params['append_to_response'] = append_to_response
        return await self._get(f'/{media_type}/{media_id}', params=params)

    async def get_recommendations(self, media_type: str, media_id: int) -> list[dict[str, Any]]:
        """Get recommendations based on a movie or TV show."""
        data = await self._get(f'/{media_type}/{media_id}/recommendations')
        return cast(list[dict[str, Any]], data.get('results', []))

    async def get_account_states(self, media_type: str, media_id: int) -> dict[str, Any]:
        """Get account states (rating, watchlist, favorite) for a movie or TV show."""
        if not self.session_id:
            return {}

        try:
            # We need to construct the URL manually because _get handles params.
            # Endpoint: /movie/{movie_id}/account_states or /tv/{tv_id}/account_states
            # Required param: session_id
            return await self._get(f'/{media_type}/{media_id}/account_states', params={'session_id': self.session_id})
        except Exception:
            return {}

    @property
    def session_id(self) -> str | None:
        return settings.tmdb_session_id

    async def rate_media(self, media_type: str, media_id: int, rating: float) -> bool:
        """Rate a movie or TV show. Rating is 0.5 to 10.0"""
        if not self.session_id:
            return False

        endpoint = (
            f'/{urllib.parse.quote(str(media_type), safe="")}/{urllib.parse.quote(str(media_id), safe="")}/rating'
        )
        # params assignment removed (unused)
        payload = {'value': rating}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Need to construct URL + query params manually for session_id because _get is for GET
                url = f'{self.BASE_URL}{endpoint}'

                # We need API KEY in params too
                query_params = {
                    'api_key': self.api_key,
                    'session_id': self.session_id,
                }

                response = await client.post(url, params=query_params, json=payload)
                response.raise_for_status()
                return True
            except httpx.HTTPError:
                return False

    async def delete_rating(self, media_type: str, media_id: int) -> bool:
        """Delete rating for a movie or TV show."""
        if not self.session_id:
            return False

        endpoint = (
            f'/{urllib.parse.quote(str(media_type), safe="")}/{urllib.parse.quote(str(media_id), safe="")}/rating'
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # DELETE requires session_id in query params
                url = f'{self.BASE_URL}{endpoint}'
                params = {'api_key': self.api_key, 'session_id': self.session_id}

                response = await client.delete(url, params=params)
                response.raise_for_status()
                return True
            except httpx.HTTPError:
                return False

    async def get_account_info(self) -> dict[str, Any]:
        """Get account details."""
        if not self.session_id:
            return {}
        return await self._get('/account', params={'session_id': self.session_id})

    async def get_rated_media(self, media_type: str = 'movies') -> list[dict[str, Any]]:
        """Get rated movies or tv shows."""
        # media_type: 'movies' or 'tv'
        account = await self.get_account_info()
        account_id = account.get('id')
        if not account_id:
            return []

        endpoint_type = 'movies' if media_type == 'movie' else 'tv'
        data = await self._get(
            f'/account/{account_id}/rated/{endpoint_type}',
            params={'session_id': self.session_id, 'sort_by': 'created_at.desc'},
        )
        return cast(list[dict[str, Any]], data.get('results', []))

    async def get_watchlist(self, media_type: str = 'movies') -> list[dict[str, Any]]:
        """Get user watchlist."""
        account = await self.get_account_info()
        account_id = account.get('id')
        if not account_id:
            return []

        endpoint_type = 'movies' if media_type == 'movie' else 'tv'
        data = await self._get(
            f'/account/{account_id}/watchlist/{endpoint_type}',
            params={'session_id': self.session_id, 'sort_by': 'created_at.desc'},
        )
        return cast(list[dict[str, Any]], data.get('results', []))

    async def add_to_watchlist(self, media_type: str, media_id: int, watchlist: bool = True) -> bool:
        """Add or remove from watchlist."""
        if not self.session_id:
            return False

        account = await self.get_account_info()
        account_id = account.get('id')
        if not account_id:
            return False

        endpoint = f'/account/{account_id}/watchlist'
        params = {'session_id': self.session_id, 'api_key': self.api_key}
        payload = {'media_type': media_type, 'media_id': media_id, 'watchlist': watchlist}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(f'{self.BASE_URL}{endpoint}', params=params, json=payload)
                response.raise_for_status()
                return True
            except httpx.HTTPError:
                return False

    async def search_movie(self, query: str, year: int | None = None) -> list[dict[str, Any]]:
        """Search specifically for movies."""
        params: dict[str, Any] = {'query': query}
        if year:
            params['year'] = year
        data = await self._get('/search/movie', params=params)
        return cast(list[dict[str, Any]], data.get('results', []))

    async def search_tv(self, query: str, year: int | None = None) -> list[dict[str, Any]]:
        """Search specifically for TV shows."""
        params: dict[str, Any] = {'query': query}
        if year:
            params['first_air_date_year'] = year
        data = await self._get('/search/tv', params=params)
        return cast(list[dict[str, Any]], data.get('results', []))

    async def get_personal_recommendations(self) -> list[dict[str, Any]]:
        """Get personalized recommendations based on rated movies/shows."""
        # 1. Get rated movies
        rated = await self.get_rated_media('movie')
        if not rated:
            # Fallback to trending
            return await self.get_trending('movie')

        # 2. Get recommendations for the most recently rated highly
        # Sort by rating (desc) then date? API sort is created_at.desc
        # Let's take the first one (most recent)
        target = rated[0]
        return await self.get_recommendations('movie', target['id'])
