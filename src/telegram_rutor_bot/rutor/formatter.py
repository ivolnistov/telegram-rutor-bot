"""Message formatting utilities for rutor parser"""

from typing import Any

from bs4 import BeautifulSoup


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


def format_torrent_message(result: dict[str, Any], soup: BeautifulSoup, imdb_rating: str, kp_rating: str) -> str:
    """Format the final torrent info message"""
    message_parts = []
    message_parts.extend(_format_title_section(result, soup))
    message_parts.extend(_format_ratings_section(imdb_rating, kp_rating))
    message_parts.append('')
    message_parts.extend(_format_movie_details(result))
    message_parts.append('')
    message_parts.extend(_format_technical_details(result))
    message_parts.extend(_format_description_section(result))

    links_part = []
    if result.get('imdb_url'):
        links_part.append(f'🔗 IMDB: {result["imdb_url"]}')
    if result.get('kp_url'):
        links_part.append(f'🔗 Кинопоиск: {result["kp_url"]}')

    if links_part:
        message_parts.append('')
        message_parts.extend(links_part)

    return '\\n'.join(message_parts)
