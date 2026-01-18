"""Parser for rutor.info torrent site with Transmission integration."""

from __future__ import annotations

import locale
import logging
import os
import re
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from hashlib import blake2s
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag
from sqlalchemy.exc import IntegrityError

from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import (
    add_torrent,
    get_or_create_film,
    get_torrent_by_blake,
    get_torrent_by_id,
    get_torrent_by_magnet,
    modify_torrent,
    update_film_metadata,
)
from telegram_rutor_bot.torrent_clients import get_torrent_client
from telegram_rutor_bot.utils.cache import FilmInfoCache
from telegram_rutor_bot.utils.category_mapper import (
    detect_category_from_title,
    map_genre_to_category,
    map_rutor_category,
)

from .rating_parser import get_imdb_poster, get_movie_ratings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from telegram_rutor_bot.db.models import Film, Torrent

log = logging.getLogger(f'{settings.log_prefix}.parser')
KINOPOISK_RE = re.compile(r'https?://www\.kinopoisk\.ru')
IMDB_RE = re.compile(r'https?://www\.imdb\.com')
FILE_LIFE_TIME = 1200

__all__ = (
    'download_torrent',
    'get_file_link',
    'get_torrent_details',
    'get_torrent_info',
    'parse_rutor',
)


def _get_client() -> httpx.AsyncClient:
    """Get or create async HTTP client"""
    proxies = None
    if settings.proxy:
        # httpx expects proxy configuration as a single proxy URL for all protocols
        proxies = settings.proxy

    return httpx.AsyncClient(
        proxy=proxies,  # Use 'proxy' instead of 'proxies'
        timeout=httpx.Timeout(settings.timeout),
        headers={
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/39.0.2171.95 Safari/537.36'
            )
        },
    )


def parse_name(name: str) -> list[str]:
    """Parse movie name to extract title and year."""
    name = name.replace('ё', 'е').replace('Ё', 'Е')
    search = re.search(r'\(([\d]{4})\)', name)
    if search:
        film = name[: search.start()]
        year = int(search.group(1))
    else:
        film = name
        year = datetime.now(UTC).year
    res = re.sub(r'\s?\[.*?\]', '', film)
    res = re.sub(r'\s?/.*', '', res)
    return [res.strip(), str(year)]


def get_torrent_node(node: Tag) -> Tag | None:
    """Extract torrent link node from a table row."""
    for anchor in node.find_all('a'):
        href = anchor.attrs.get('href', None)
        if not href:
            continue
        if href.startswith('/torrent'):
            return cast(Tag, anchor)
    return None


def size_to_bytes_converter(string: str) -> int:
    """Convert size string (KB/MB/GB) to bytes."""
    if string.endswith('GB'):
        size_str = string[:-2].strip()
        size = float(size_str) * 1024 * 1024 * 1024
    elif string.endswith('MB'):
        size_str = string[:-2].strip()
        size = float(size_str) * 1024 * 1024
    elif string.endswith('KB'):
        size_str = string[:-2].strip()
        size = float(size_str) * 1024
    else:
        size = 0
    return int(size)


@contextmanager
def localize(cat: int, loc: str) -> Iterator[str]:
    """Context manager to temporarily change locale."""
    old_locale = locale.setlocale(cat)
    try:
        yield locale.setlocale(cat, loc)
    finally:
        locale.setlocale(cat, old_locale)


def _extract_torrent_data(lnk: Tag) -> dict[str, Any] | None:
    """Extract torrent data from link element"""
    if not lnk.parent or not lnk.parent.parent:
        return None
    row = lnk.parent.parent
    if not hasattr(row, 'find_all'):
        return None
    tds = row.find_all('td')
    size = size_to_bytes_converter(tds[-2].get_text())

    try:
        date = datetime.strptime(tds[0].get_text(), '%d\xa0%b\xa0%y').replace(tzinfo=UTC).date()
    except ValueError:
        date = datetime.now(UTC).date()

    magnet = lnk.attrs['href']
    parent = lnk.parent
    if not parent:
        return None
    torrent = get_torrent_node(parent)
    if not torrent:
        return None

    torrent_lnk = torrent.attrs['href']
    torrent_lnk_blake = blake2s(torrent_lnk.encode()).hexdigest()
    text = parse_name(torrent.get_text())
    year = text.pop()
    name = text[0]
    blake = blake2s(name.encode()).hexdigest()

    return {
        'size': size,
        'date': date,
        'magnet': magnet,
        'torrent': torrent,
        'torrent_lnk': torrent_lnk,
        'torrent_lnk_blake': torrent_lnk_blake,
        'year': year,
        'name': name,
        'blake': blake,
    }


async def _process_torrent_item(
    session: AsyncSession,
    torrent_data: dict[str, Any],
    film_cache: dict[str, int],
    new: list[int],
    category_id: int | None = None,
) -> None:
    """Process a single torrent item"""
    # Get or create film
    film_id = film_cache.get(torrent_data['blake'])
    if not film_id:
        film = await get_or_create_film(
            session, torrent_data['blake'], int(torrent_data['year']), torrent_data['name'], category_id=category_id
        )
        film_id = film.id
        film_cache[torrent_data['blake']] = film_id
        if film.id not in new:
            new.append(film_id)

    try:
        await add_torrent(
            session,
            film_id=film_id,
            blake=torrent_data['torrent_lnk_blake'],
            name=torrent_data['torrent'].get_text(),
            magnet=torrent_data['magnet'],
            created=datetime.combine(torrent_data['date'], datetime.min.time()).replace(tzinfo=UTC),
            link=torrent_data['torrent_lnk'],
            sz=torrent_data['size'],
            approved=False,
            downloaded=False,
        )
    except IntegrityError:
        # Torrent with this magnet already exists, update it
        existing = await get_torrent_by_magnet(session, torrent_data['magnet'])
        if existing:
            await modify_torrent(
                session,
                torrent_id=existing.id,
                name=torrent_data['torrent'].get_text(),
                sz=torrent_data['size'],
            )
        await session.commit()

    # Enrich film data if missing poster
    # We do this after committing the torrent to ensure basic data is saved
    # even if enrichment fails or is slow.
    # We only enrich if we have the film object (i.e. it wasn't cached)
    if 'film' in locals() and film and not film.poster:
        await enrich_film_data(session, film, torrent_data['torrent_lnk'])


async def parse_rutor(
    url: str,
    session: AsyncSession,
    category_id: int | None = None,
    progress_callback: Callable[[int], Awaitable[None]] | None = None,
) -> list[int]:
    """Parse rutor.info search results and save to database."""
    async with _get_client() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.text
        except httpx.InvalidURL as e:
            raise ValueError('invalid url ' + url) from e

    soup = BeautifulSoup(data, 'lxml')
    new: list[int] = []
    film_cache: dict[str, int] = {}

    with localize(locale.LC_ALL, os.getenv('HTML_LOCALE', 'ru_RU.UTF-8')):
        body = soup.body
        if not body:
            return []

        links = [
            lnk
            for lnk in body.find_all('a')
            if lnk.attrs.get('href', '') and lnk.attrs.get('href', '').startswith('magnet')
        ]
        total_links = len(links)

        for i, lnk in enumerate(links):
            # Report progress
            if progress_callback and total_links > 0:
                # Progress from 10% to 90%
                progress = 10 + int((i / total_links) * 80)
                await progress_callback(progress)

            # Extract torrent data
            torrent_data = _extract_torrent_data(lnk)
            if not torrent_data:
                continue

            # Skip if size limit exceeded
            if settings.size_limit and int(torrent_data['size']) > settings.size_limit:
                continue

            # Check if torrent already exists
            existing_torrent = await get_torrent_by_blake(session, torrent_data['torrent_lnk_blake'])
            if existing_torrent:
                continue

            # Process torrent
            await _process_torrent_item(session, torrent_data, film_cache, new, category_id)

    return new


async def enrich_film_data(session: AsyncSession, film: Film, torrent_link: str) -> None:
    """Fetch additional film data (poster, ratings) from torrent page."""
    try:
        # We pass a dummy download command as we only need metadata
        _info, _poster, _images, poster_url, metadata = await get_torrent_info(torrent_link)
        updates: dict[str, Any] = {}
        if poster_url and not film.poster:
            updates['poster'] = poster_url

        # Update other metadata if available
        if metadata:
            if metadata.get('country'):
                updates['country'] = metadata['country']
            if metadata.get('genre'):
                updates['genres'] = metadata['genre']
            if metadata.get('year'):
                with suppress(ValueError):
                    updates['year'] = int(metadata['year'])

        if updates:
            await update_film_metadata(session, film.id, **updates)

    except (ValueError, TypeError, AttributeError, ConnectionError) as e:
        log.warning('Failed to enrich film %s: %s', film.name, e)


async def get_torrent_details(session: AsyncSession, torrent_id: int) -> dict[str, Any]:
    """Get detailed torrent information from rutor page."""
    torrent = await get_torrent_by_id(session, torrent_id)
    if not torrent:
        return {}
    page_link = urljoin('http://www.rutor.info', torrent.link)

    async with _get_client() as client:
        response = await client.get(page_link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

    result = {}
    for link in soup.find_all('a'):
        url = link.attrs.get('href')
        if url and has_good_link(url):
            result['url'] = url
    links = soup.find_all(id='details')[0]
    links = links.find_all('tr')
    for row in links:
        field_name = row.find_all('td')[0].text.strip()
        field_value = row.find_all('td')[1].text.strip()
        if 'описание' in field_name.lower():
            result['description'] = field_value
        elif 'видео' in field_name.lower():
            result['video_quality'] = field_value
        elif 'качество' in field_name.lower():
            result['quality'] = field_value
        elif 'перевод' in field_name.lower():
            result['translate_quality'] = field_value
        elif 'субтитры' in field_name.lower():
            result['subtitles'] = field_value
    return result


def has_good_link(source: str) -> bool:
    """Check if URL is a valid IMDB or Kinopoisk link."""
    if IMDB_RE.match(source):
        return True
    return bool(KINOPOISK_RE.match(source))


async def get_file_link(link: str) -> str:
    """Get torrent file download link from torrent page."""
    page = urljoin('http://www.rutor.info', link)
    async with _get_client() as client:
        response = await client.get(page)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

    for anchor in soup.find_all('a'):
        url = anchor.attrs.get('href')
        if url and url.startswith('/download'):
            return str(urljoin('http://rutor.info', url))
    return ''


def _extract_movie_links(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Extract IMDB and Kinopoisk URLs from the page"""
    imdb_url = None
    kp_url = None

    for link in soup.find_all('a'):
        url = link.attrs.get('href', '')
        if url:
            if IMDB_RE.match(url):
                imdb_url = url
            elif KINOPOISK_RE.match(url):
                kp_url = url

    return imdb_url, kp_url


def _extract_details_from_table(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract movie details from the details table"""
    result: dict[str, Any] = {}
    details_div = soup.find(id='details')
    if not details_div or not isinstance(details_div, Tag):
        return result

    rows = details_div.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            field_name = cells[0].text.strip()
            field_value = cells[1].text.strip()
            # Skip empty field names
            if not field_name or field_name == ':':
                continue

            _process_field(field_name, field_value, result)

    return result


def _process_field(field_name: str, field_value: str, result: dict[str, Any]) -> None:
    """Process a single field from the movie details"""
    field_lower = field_name.lower()

    # Field mappings
    field_mappings = {
        'description': ['описание'],
        'title': ['название'],
        'original_title': ['оригинальное название'],
        'year': ['год'],
        'country': ['страна'],
        'genre': ['жанр'],
        'duration': ['продолжительность', 'время'],
        'director': ['режиссер'],
        'actors': ['актеры', 'в ролях'],
        'video_quality': ['видео'],
        'quality': ['качество'],
        'translate_quality': ['перевод'],
        'subtitles': ['субтитры'],
        'audio': ['аудио'],
    }

    # Process field using mapping
    for result_key, patterns in field_mappings.items():
        if any(pattern in field_lower for pattern in patterns):
            result[result_key] = field_value
            break


def _extract_movie_info_from_blocks(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract movie info from special blocks on the page"""
    result: dict[str, Any] = {}

    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if not cells:
            continue

        # Check both cells for movie info
        cell_text = cells[1].text if len(cells) > 1 else cells[0].text
        if 'Информация о фильме' not in cell_text:
            continue

        # Parse movie info from the cell text
        _parse_movie_info_text(cell_text, result)
        break

    return result


def _parse_movie_info_text(cell_text: str, result: dict[str, Any]) -> None:
    """Parse movie info from cell text"""
    lines = cell_text.split('\n')
    for line in lines:
        if ':' in line:
            field_name, field_value = line.split(':', 1)
            field_name = field_name.strip()
            field_value = field_value.strip()

            _process_movie_field(field_name, field_value, result)
        elif line.startswith('О фильме'):
            # Extract description
            desc_idx = lines.index(line)
            if desc_idx + 1 < len(lines):
                result['description'] = _extract_description(lines, desc_idx + 1)


def _process_movie_field(field_name: str, field_value: str, result: dict[str, Any]) -> None:
    """Process a movie field from the info block"""
    # Direct field mappings
    field_mappings = {
        'Название': 'title',
        'Оригинальное название': 'original_title',
        'Год выпуска': 'year',
        'Год выхода': 'year',
        'Жанр': 'genre',
        'Режиссер': 'director',
        'Режиссёр': 'director',
        'В ролях': 'actors',
        'Страна': 'country',
        'Продолжительность': 'duration',
        'Качество': 'quality',
        'Видео': 'video_quality',
        'Субтитры': 'subtitles',
    }

    # Handle special case for audio
    if field_name.startswith('Аудио'):
        if 'audio' not in result:
            result['audio'] = []
        result['audio'].append(field_value)
        return

    # Use mapping to set field
    if field_name in field_mappings:
        result[field_mappings[field_name]] = field_value


def _extract_description(lines: list[str], start_idx: int) -> str:
    """Extract description from lines starting at given index"""
    desc_lines = []
    for desc_line in lines[start_idx:]:
        stripped_line = desc_line.strip()
        if stripped_line and not stripped_line.endswith(':') and not stripped_line.startswith('Качество'):
            desc_lines.append(stripped_line)
        elif stripped_line.endswith(':') or stripped_line.startswith('Качество'):
            break
    return ' '.join(desc_lines)


async def _extract_images(soup: BeautifulSoup, imdb_url: str | None) -> tuple[str | None, bytes | None, list[bytes]]:
    """Extract poster and screenshots from the page"""
    poster_url = None
    poster = None
    images: list[bytes] = []

    # If no poster found on page, try to get from IMDB
    if imdb_url:
        poster, poster_url_from_imdb = await get_imdb_poster(imdb_url)
        if poster_url_from_imdb:
            poster_url = poster_url_from_imdb

    # Try to extract poster and screenshots
    async with _get_client() as client:
        for img in soup.find_all('img'):
            src = img.attrs.get('src', '')
            if not src or not any(host in src for host in ['poster', 'fastpic', 'radikal', 'imageban', 'lostpix']):
                continue

            try:
                # Handle relative URLs
                if src.startswith('//'):
                    src = 'http:' + src
                elif src.startswith('/'):
                    src = urljoin('http://www.rutor.info', src)

                img_response = await client.get(src, timeout=5)
                img_response.raise_for_status()
                img_data = img_response.content

                # First large image or one with 'poster' in name is likely the poster
                if poster is None and _is_poster_image(src, img_data, len(images)):
                    poster = img_data
                    poster_url = src
                else:
                    images.append(img_data)
            except (httpx.HTTPError, OSError, ValueError):
                # Skip unavailable images (e.g., radikal.ru is down)
                pass

    return poster_url, poster, images


def _is_poster_image(src: str, img_data: bytes, current_images_count: int) -> bool:
    """Check if an image is likely a poster"""
    return (
        'poster' in src.lower()
        or 'cover' in src.lower()
        or ('imageban' in src and current_images_count == 0)  # First imageban image is often poster
        or len(img_data) > 100000  # Large images are likely posters
    )


def _format_title_section(result: dict[str, Any], soup: BeautifulSoup) -> list[str]:
    """Format title section of the message"""
    message_parts = []

    if 'title' in result:
        title_line = f'🎬 {result["title"]}'
        if 'year' in result:
            title_line += f' ({result["year"]})'
        message_parts.append(title_line)

        # Add original title if different
        if 'original_title' in result and result['original_title'] != result['title']:
            message_parts.append(f'🌍 {result["original_title"]}')
    else:
        # Try to extract title from page
        title_tag = soup.find('title')
        if title_tag:
            page_title = title_tag.text.strip()
            # Clean up the title
            page_title = (
                page_title.replace(' :: RuTor.info', '').replace(' :: Rutor', '').replace(' :: rutor.info', '').strip()
            )
            if page_title:
                message_parts.append(f'🎬 {page_title}')

    return message_parts


def _format_ratings_section(imdb_rating: str | None, kp_rating: str | None) -> list[str]:
    """Format ratings section of the message"""
    rating_parts = []
    if imdb_rating:
        rating_parts.append(f'⭐ IMDB: {imdb_rating}/10')
    if kp_rating:
        rating_parts.append(f'⭐ Кинопоиск: {kp_rating}/10')

    if rating_parts:
        return [' | '.join(rating_parts)]
    return []


def _format_movie_details(result: dict[str, Any]) -> list[str]:
    """Format movie details section"""
    message_parts = []

    detail_fields = [
        ('genre', '📁 Жанр: {}'),
        ('country', '🌍 Страна: {}'),
        ('duration', '⏱ Продолжительность: {}'),
        ('director', '🎭 Режиссер: {}'),
    ]

    for field, template in detail_fields:
        if field in result:
            message_parts.append(template.format(result[field]))

    if 'actors' in result:
        actors = result['actors'][:150] + '...' if len(result['actors']) > 150 else result['actors']
        message_parts.append(f'👥 В ролях: {actors}')

    return message_parts


def _format_technical_details(result: dict[str, Any]) -> list[str]:
    """Format technical details section"""
    message_parts = ['📀 Технические детали:']

    if 'quality' in result:
        message_parts.append(f'💎 Качество: {result["quality"]}')
    if 'video_quality' in result:
        message_parts.append(f'📹 Видео: {result["video_quality"]}')
    if 'audio' in result:
        for i, audio in enumerate(result['audio'], 1):
            message_parts.append(f'🎙 Аудио {i}: {audio}')
    elif 'translate_quality' in result:
        message_parts.append(f'🎙 Перевод: {result["translate_quality"]}')
    if 'subtitles' in result:
        message_parts.append(f'💬 Субтитры: {result["subtitles"]}')

    return message_parts


def _format_description_section(result: dict[str, Any]) -> list[str]:
    """Format description section"""
    message_parts = []

    if 'description' in result:
        message_parts.extend(['', '📝 Описание:'])
        desc = result['description'][:500] + '...' if len(result['description']) > 500 else result['description']
        message_parts.append(desc)

    return message_parts


def _format_links_section(download_command: str, imdb_url: str | None, kp_url: str | None, page_link: str) -> list[str]:
    """Format links section"""
    message_parts = ['', f'💾 Скачать: {download_command}']

    if imdb_url:
        message_parts.append(f'🔗 IMDB: {imdb_url}')
    if kp_url:
        message_parts.append(f'🔗 Кинопоиск: {kp_url}')
    message_parts.append(f'🔗 Rutor: {page_link}')

    return message_parts


async def get_torrent_info(
    torrent_link: str,
) -> tuple[str, bytes | None, list[bytes], str | None, dict[str, Any]]:
    """Get torrent info from rutor page, including poster, images and metadata"""
    # Use torrent_link as cache key
    cache = FilmInfoCache()
    cache_key = torrent_link

    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        # Reconstruct the return values from cached data
        message = cached_data.get('message', '')
        poster_data = cached_data.get('poster')
        poster = bytes.fromhex(poster_data) if poster_data else None
        images_data = cached_data.get('images', [])
        images = [bytes.fromhex(img) for img in images_data]
        poster_url = cached_data.get('poster_url')
        metadata = cached_data.get('metadata', {})
        return message, poster, images, poster_url, metadata

    page_link = urljoin('http://www.rutor.info', torrent_link)

    async with _get_client() as client:
        response = await client.get(page_link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

    # Extract movie links and basic details
    imdb_url, kp_url = _extract_movie_links(soup)
    result = _extract_details_from_table(soup)

    if imdb_url:
        result['imdb_url'] = imdb_url
    if kp_url:
        result['kp_url'] = kp_url

    # Look for movie information in special blocks
    result.update(_extract_movie_info_from_blocks(soup))

    # Get ratings from IMDB and Kinopoisk
    imdb_rating, kp_rating = await get_movie_ratings(imdb_url, kp_url)

    # Extract poster and images
    poster_url, poster, images = await _extract_images(soup, imdb_url)

    # Format message using helper functions
    message_parts = []

    # Title section
    message_parts.extend(_format_title_section(result, soup))

    # Ratings section
    message_parts.extend(_format_ratings_section(imdb_rating, kp_rating))

    # Empty line
    message_parts.append('')

    # Movie details
    message_parts.extend(_format_movie_details(result))

    # Empty line
    message_parts.append('')

    # Technical details
    message_parts.extend(_format_technical_details(result))

    # Description
    message_parts.extend(_format_description_section(result))

    message = '\n'.join(message_parts)

    # Metadata for enrichment
    metadata = {
        'country': result.get('country'),
        'genre': result.get('genre'),
        'year': result.get('year'),
        'imdb_url': result.get('imdb_url'),
        'kp_url': result.get('kp_url'),
    }

    # Cache the result
    cache_data = {
        'message': message,
        'poster': poster.hex() if poster else None,
        'images': [img.hex() for img in images[:3]],  # Limit to 3 images
        'poster_url': poster_url,
        'metadata': metadata,
    }
    cache.set(cache_key, cache_data)

    return message, poster, images[:3], poster_url, metadata


def _extract_genre_from_details(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Extract genre and category from details section"""
    genre = None
    rutor_category = None

    details_div = soup.find(id='details')
    if details_div and isinstance(details_div, Tag):
        for row in details_div.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                field_name = cells[0].text.strip()
                if 'жанр' in field_name.lower():
                    genre = cells[1].text.strip()
                elif 'категория' in field_name.lower():
                    rutor_category = cells[1].text.strip()

    return genre, rutor_category


def _extract_genre_from_movie_block(soup: BeautifulSoup) -> str | None:
    """Extract genre from movie info block"""
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if cells:
            cell_text = cells[1].text if len(cells) > 1 else cells[0].text
            if 'Жанр:' in cell_text:
                lines = cell_text.split('\n')
                for line in lines:
                    if line.strip().startswith('Жанр:'):
                        genre = line.split(':', 1)[1].strip()
                        return genre if genre else None
    return None


def _determine_category(genre: str | None, rutor_category: str | None, torrent_name: str) -> str | None:
    """Determine category based on genre, rutor category and torrent name"""
    # Try rutor category first
    category = map_rutor_category(rutor_category)

    # Try genre mapping - it's usually more accurate
    if not category:
        category = map_genre_to_category(genre)

    # For series, title patterns can help when genre is generic
    if not category or (
        category == 'FILMS'
        and genre
        and any(word in genre.lower() for word in ['драма', 'криминал', 'триллер', 'боевик'])
    ):
        title_category = detect_category_from_title(torrent_name)
        if title_category == 'TVSHOWS':
            category = title_category

    # Final fallback to title detection
    if not category:
        category = detect_category_from_title(torrent_name)

    return category


async def download_torrent(torrent: Torrent) -> dict[str, Any]:
    """Download torrent using configured torrent client"""
    category = None

    try:
        # Get torrent details page
        page_link = urljoin('http://www.rutor.info', torrent.link)
        async with _get_client() as client:
            response = await client.get(page_link)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')

        # Extract genre and category
        genre, rutor_category = _extract_genre_from_details(soup)

        # Also check in movie info block if genre not found
        if not genre:
            genre = _extract_genre_from_movie_block(soup)

        # Determine category
        category = _determine_category(genre, rutor_category, torrent.name)

    except (httpx.HTTPError, OSError, ValueError, KeyError, AttributeError):
        # If we can't get genre, try to detect from torrent name
        category = detect_category_from_title(torrent.name)

    # Determine download directory from category
    download_dir = None
    if torrent.film and torrent.film.category_rel and torrent.film.category_rel.folder:
        download_dir = torrent.film.category_rel.folder

    # Download the torrent
    torrent_client = get_torrent_client()
    try:
        await torrent_client.connect()
        return await torrent_client.add_torrent(
            torrent.magnet,
            download_dir=download_dir,
            category=category,
            rename=torrent.name,
        )
    finally:
        await torrent_client.disconnect()
