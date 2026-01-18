"""Parser for getting movie ratings from IMDB and Kinopoisk"""

import re

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag


async def get_imdb_rating(imdb_url: str) -> dict[str, str]:
    """Get rating from IMDB page"""
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            response = await client.get(imdb_url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # Try multiple selectors for different IMDB layouts
            selectors = [
                {'name': 'span', 'attrs': {'itemprop': 'ratingValue'}},
                {'name': 'span', 'attrs': {'class': 'sc-bde20123-1'}},
                {'name': 'span', 'attrs': {'data-testid': 'ratingGroup--imdb-rating'}},
                {'name': 'div', 'attrs': {'data-testid': 'hero-rating-bar__aggregate-rating__score'}},
                {'name': 'span', 'attrs': {'class': re.compile(r'AggregateRatingButton__RatingScore')}},
            ]

            for selector in selectors:
                element = soup.find(selector['name'], selector.get('attrs', {}))
                if element:
                    # Extract rating text
                    rating_text = element.get_text(strip=True)
                    # Extract just the number (e.g., "8.5/10" -> "8.5")
                    match = re.search(r'(\d+\.?\d*)', rating_text)
                    if match:
                        return {'rating': match.group(1), 'source': 'IMDB'}

    except (httpx.HTTPError, AttributeError, ValueError):
        # COMMENT: Silently ignore HTTP errors, parsing errors, and missing attributes
        pass

    return {}


async def get_kinopoisk_rating(kp_url: str) -> dict[str, str]:
    """Get rating from Kinopoisk page"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = await client.get(kp_url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # Try to find rating
            rating_element = soup.find('span', class_='film-rating-value')
            if not rating_element:
                rating_element = soup.find('span', {'class': re.compile('rating__value')})

            if rating_element:
                rating = rating_element.text.strip()
                return {'rating': rating, 'source': 'Кинопоиск'}

    except (httpx.HTTPError, AttributeError, ValueError):
        # COMMENT: Silently ignore HTTP errors, parsing errors, and missing attributes
        pass

    return {}


async def get_imdb_poster(imdb_url: str) -> tuple[bytes | None, str | None]:
    """Get poster from IMDB page"""
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            response = await client.get(imdb_url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # Find poster image
            poster_img = soup.find('img', {'class': re.compile('ipc-image')})
            if not poster_img:
                # Try alternate selector
                poster_div = soup.find('div', {'class': 'ipc-poster'})
                if poster_div and hasattr(poster_div, 'find'):
                    img_tag = poster_div.find('img')
                    if isinstance(img_tag, Tag):
                        poster_img = img_tag

            if poster_img and isinstance(poster_img, Tag) and poster_img.get('src'):
                poster_url_raw = poster_img['src']
                # Handle case where BeautifulSoup returns a list
                poster_url: str | None = None
                if isinstance(poster_url_raw, list):
                    poster_url = poster_url_raw[0] if poster_url_raw else None
                elif isinstance(poster_url_raw, str):
                    poster_url = poster_url_raw

                if poster_url:
                    # Get higher resolution version
                    if '._V1_' in poster_url:
                        poster_url = poster_url.split('._V1_')[0] + '._V1_FMjpg_UX600_.jpg'

                    # Return URL without downloading
                    return None, poster_url

    except (httpx.HTTPError, AttributeError, ValueError):
        # COMMENT: Silently ignore HTTP errors, parsing errors, and missing attributes
        pass

    return None, None


async def get_movie_ratings(imdb_url: str | None = None, kp_url: str | None = None) -> tuple[str, str]:
    """Get ratings from both IMDB and Kinopoisk"""
    imdb_rating = ''
    kp_rating = ''

    if imdb_url:
        result = await get_imdb_rating(imdb_url)
        if result:
            rating = result.get('rating')
            if rating:
                imdb_rating = rating

    if kp_url:
        result = await get_kinopoisk_rating(kp_url)
        if result:
            rating = result.get('rating')
            if rating:
                kp_rating = rating

    return imdb_rating, kp_rating
