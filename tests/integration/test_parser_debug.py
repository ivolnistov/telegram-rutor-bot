"""Debug parser test"""

from urllib.parse import urljoin

import pytest
from bs4 import BeautifulSoup

from telegram_rutor_bot.rutor.parser import _get_client, get_torrent_info


@pytest.mark.asyncio
async def test_debug_parse_torrent():
    """Debug parsing torrent page"""
    torrent_link = '/torrent/840427/mama-vozvrawenie-iz-tmy_the-unlit-2020-web-dl-1080p-itunes'
    page_link = urljoin('http://www.rutor.info', torrent_link)

    print(f'\nFetching: {page_link}')

    async with _get_client() as client:
        response = await client.get(page_link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

    # Check title
    title_tag = soup.find('title')
    if title_tag:
        print(f'\nPage title: {title_tag.text}')

    # Check for details div
    details_div = soup.find(id='details')
    print(f'\nFound details div: {details_div is not None}')

    if details_div:
        rows = details_div.find_all('tr')
        print(f'Number of rows in details: {len(rows)}')

        for i, row in enumerate(rows[:5]):  # First 5 rows
            cells = row.find_all('td')
            if len(cells) >= 2:
                field = cells[0].text.strip()
                value = cells[1].text.strip()[:50]  # First 50 chars
                print(f"Row {i}: '{field}' = '{value}'")

    # Check for movie info
    print("\n--- Looking for 'Информация о фильме' ---")
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if cells:
            text = cells[0].text.strip()
            if 'Информация о фильме' in text:
                print(f'Found: {text}')
                # Look at next rows
                next_row = row.find_next_sibling('tr')
                count = 0
                while next_row and count < 5:
                    cells = next_row.find_all('td')
                    if len(cells) >= 2:
                        field = cells[0].text.strip()
                        value = cells[1].text.strip()[:50]
                        print(f'  {field}: {value}')
                    next_row = next_row.find_next_sibling('tr')
                    count += 1

    # Check for links
    print('\n--- Links ---')
    for link in soup.find_all('a'):
        href = link.get('href', '')
        if 'imdb.com' in href or 'kinopoisk.ru' in href:
            print(f'Found: {href}')

    # Now test actual parser
    print('\n--- Testing get_torrent_info ---')
    message, poster, images = await get_torrent_info(torrent_link, '/dl_100')
    print(f'\nMessage length: {len(message)}')
    print(f'Has poster: {poster is not None}')
    print(f'Number of images: {len(images)}')
