"""Debug parser to see what's on the torrent page"""

import asyncio
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


async def debug_torrent_page(link: str) -> BeautifulSoup:
    """Debug function to see what's on the torrent page"""
    page_link = urljoin('http://www.rutor.info', link)

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(page_link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

    title = soup.find('title')
    if title:
        pass

    for anchor in soup.find_all('a'):
        href = anchor.attrs.get('href', '')
        if 'imdb.com' in href or 'kinopoisk.ru' in href:
            pass

    details_div = soup.find(id='details')
    if details_div and hasattr(details_div, 'find_all'):
        rows = details_div.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                cells[0].text.strip()
                _ = cells[1].text.strip()[:100]  # Limit to 100 chars
    else:
        pass

    for img in soup.find_all('img'):
        src = img.attrs.get('src', '')
        if 'poster' in src or 'fastpic' in src or 'radikal' in src:
            pass

    # Find main content area
    main_content = soup.find('div', {'id': 'content'}) or soup.find('div', {'class': 'content'})
    if main_content:
        # Look for any div with movie information
        for div in main_content.find_all('div') if hasattr(main_content, 'find_all') else []:
            text = div.text.strip()
            if len(text) > 50 and ('Описание' in text or 'описание' in text):
                pass

    return soup


if __name__ == '__main__':
    # Test with a specific torrent
    TORRENT_LINK = '/torrent/840427/mama-vozvrawenie-iz-tmy_the-unlit-2020-web-dl-1080p-itunes'
    asyncio.run(debug_torrent_page(TORRENT_LINK))
