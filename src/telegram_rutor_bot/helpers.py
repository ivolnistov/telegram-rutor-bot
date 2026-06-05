"""Helper functions for the bot"""

import html
import logging
import re
from collections.abc import Iterable
from hashlib import blake2s
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram_rutor_bot.clients.tmdb import TmdbClient
from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import get_async_session, get_films_by_ids, get_torrents_by_film, update_film_metadata
from telegram_rutor_bot.rutor import get_torrent_info
from telegram_rutor_bot.rutor.constants import RUTOR_BASE_URL
from telegram_rutor_bot.schemas import Notification
from telegram_rutor_bot.utils.episode_parser import EpisodeInfo, format_episode_label

_tmdb = TmdbClient()
_CAST_LIMIT = 5

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from telegram_rutor_bot.db.models import Film, Torrent


def gen_hash(text: str, prefix: str | None = None) -> str:
    """Generate a blake2s hash from text with optional prefix"""
    return (prefix or '') + blake2s(text.encode()).hexdigest()


def humanize_bytes(num: float, suffix: str = 'B') -> str:
    """Convert bytes to human readable format"""
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1000.0:
            return f'{num:3.1f} {unit}{suffix}'
        num /= 1000.0
    return f'{num:.1f} Y{suffix}'


_YEAR_PREFIX_RE = re.compile(r'^.*?\((19|20)\d{2}(?:[‐-―\-]\d{2,4})?\)\s*')


def _clean_torrent_name(torrent_name: str, film_name: str, film_year: int) -> str:
    """Strip the localized + original title and any `(YYYY)` / `(YYYY-YYYY)` prefix.

    Most rutor releases follow the pattern
        `<RU title> / <Original title> (<year>[-<end_year>]) <release info>`
    so the cheapest cleanup is to drop everything up to and including the first year
    parenthesis. The legacy regexes below handle the rare cases where the year is
    missing entirely (e.g. cartoons indexed without a release year).
    """
    cleaned = _YEAR_PREFIX_RE.sub('', torrent_name).strip()
    if cleaned and cleaned != torrent_name:
        return cleaned
    # Fallback — torrent without parenthesized year. Strip film name + year tokens directly.
    cleaned = re.sub(rf'^{re.escape(film_name)}\s*\({film_year}\)\s*', '', torrent_name)
    return re.sub(rf'^{re.escape(film_name)}\s+{film_year}\s+', '', cleaned).strip()


def _sort_keywords() -> list[str]:
    """Pull case-folded keywords from `settings.torrent_sort_keywords`.

    Comma-separated string, surrounding whitespace stripped, empty entries dropped.
    Lower-cased once here so the per-torrent scorer doesn't repeat the work.
    """
    raw = getattr(settings, 'torrent_sort_keywords', None) or ''
    return [k.strip().lower() for k in raw.split(',') if k.strip()]


def _keyword_match_count(name: str, keywords: list[str]) -> int:
    """Substring match count, case-insensitive. `keywords` must already be lower-cased."""
    if not keywords or not name:
        return 0
    lowered = name.lower()
    return sum(1 for kw in keywords if kw in lowered)


def _sorted_torrents(torrents: list[Torrent], film: Film | None = None) -> list[Torrent]:
    """Sort torrents for display.

    Primary axis (configurable, applied within season/episode for tv):
      1. **Keyword match count** (descending) — `settings.torrent_sort_keywords`
         lets the user prefer specific release groups, voice studios, quality tokens.
      2. **Seeds** (descending).
      3. **Size** (ascending — smaller is faster to fetch).

    For tv, `(season, episode)` stays as the outer key so the natural sequence is
    preserved; multi-season packs (no parsed `season`) sink to the end via `inf`.
    With no keywords configured, the seeds/size triple still kicks in — meaning
    seedier and smaller releases now win ties (older behaviour was size-first only).
    """
    keywords = _sort_keywords()

    def _quality_key(t: Torrent) -> tuple[int, int, int]:
        # Negate "more is better" axes so Python's ascending sort puts them first.
        score = _keyword_match_count(t.name or '', keywords)
        seeds = t.seeds or 0
        size = t.sz or 0
        return (-score, -seeds, size)

    is_tv = bool(film and film.tmdb_media_type == 'tv')
    if is_tv:
        return sorted(
            torrents,
            key=lambda t: (
                t.season if t.season is not None else float('inf'),
                t.episode or 0,
                *_quality_key(t),
            ),
        )
    return sorted(torrents, key=_quality_key)


def _episode_tag(t: Torrent) -> str:
    """`S01E02` / `S01` / `` based on what the parser stored on the torrent."""
    season = t.season
    episode = t.episode
    if season and episode:
        return f'S{int(season):02d}E{int(episode):02d}'
    if season:
        return f'S{int(season):02d}'
    return ''


_NUM_BUTTON_EMOJI = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
_BUTTONS_PER_ROW = 2


def _format_torrents_lines(torrents: list[Torrent], film: Film) -> str:
    """Render a numbered list of releases — one HTML line per torrent.

    Each line is `<numeric_emoji> <a href="rutor_url">size · seeds · tag · release</a>`.
    The HTML anchor doesn't truncate (unlike inline-button labels), so the full
    distinguishing info stays visible AND tappable to open rutor.
    """
    sorted_t = _sorted_torrents(torrents, film)
    if not sorted_t:
        return ''

    lines: list[str] = ['📥 <b>Раздачи:</b>']
    for idx, t in enumerate(sorted_t):
        prefix = _NUM_BUTTON_EMOJI[idx] if idx < len(_NUM_BUTTON_EMOJI) else f'{idx + 1}.'
        size = humanize_bytes(t.size).replace(' ', '')
        seeds_value = getattr(t, 'seeds', None)
        bits: list[str] = [size]
        if seeds_value is not None:
            bits.append(f'🌱{seeds_value}')
        tag = _episode_tag(t)
        if tag:
            bits.append(tag)
        clean = _clean_torrent_name(t.name, film.name, film.year).strip()
        clean = clean.replace('1080p ', '').replace(' 1080p', '').strip()
        if clean:
            bits.append(clean)

        body = ' · '.join(bits)
        rutor_url = urljoin(RUTOR_BASE_URL, t.link)
        link = f'<a href="{html.escape(rutor_url, quote=True)}">{html.escape(body)}</a>'
        lines.append(f'{prefix} {link}')

    return '\n'.join(lines)


def _format_torrents_buttons(torrents: list[Torrent], film: Film) -> InlineKeyboardMarkup:
    """Number + size + seeds on each button — paired with the per-line list in caption.

    Layout per button: `{number_emoji} {size} 🌱{seeds}` (e.g. `1️⃣ 14.7GB 🌱29`).
    Two per row keeps each button wide enough that the size and seed count survive
    Telegram's per-button truncation on narrow phones.
    """
    sorted_torrents = _sorted_torrents(torrents, film)
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for idx, t in enumerate(sorted_torrents):
        num = _NUM_BUTTON_EMOJI[idx] if idx < len(_NUM_BUTTON_EMOJI) else f'{idx + 1}'
        size = humanize_bytes(t.size).replace(' ', '')
        seeds_value = getattr(t, 'seeds', None)
        seeds_part = f' 🌱{seeds_value}' if seeds_value is not None else ''
        label = f'{num} {size}{seeds_part}'
        row.append(InlineKeyboardButton(label, callback_data=f'dl_{t.id}'))
        if len(row) == _BUTTONS_PER_ROW:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


async def _fetch_tmdb_details(film: Film) -> dict[str, Any]:
    """Best-effort live TMDB details fetch with credits — empty dict on any error."""
    if not film.tmdb_id:
        return {}
    media_type = film.tmdb_media_type or 'movie'
    try:
        return await _tmdb.get_details(media_type, film.tmdb_id, append_to_response='credits')
    # External API; debug-log only — transport hiccups shouldn't spam warnings
    # while users are browsing the library.
    except Exception as e:  # pylint: disable=broad-exception-caught
        log.debug('TMDB details fetch failed for film %s: %s', film.id, e)
        return {}


def _format_runtime(minutes: int | None) -> str | None:
    """Render TMDB runtime (minutes) as `Xh Ymin` (e.g. 87 → `1ч 27мин`)."""
    if not minutes or minutes <= 0:
        return None
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f'{hours}ч {mins:02d}мин'
    if hours:
        return f'{hours}ч'
    return f'{mins}мин'


def _runtime_from_details(details: dict[str, Any]) -> int | None:
    """TMDB stores `runtime` for movies (single int) and `episode_run_time` for tv (list[int])."""
    runtime = details.get('runtime')
    if isinstance(runtime, int) and runtime > 0:
        return runtime
    ep_runs = details.get('episode_run_time')
    if isinstance(ep_runs, list) and ep_runs and isinstance(ep_runs[0], int):
        return ep_runs[0]
    return None


def _genres_from_details(details: dict[str, Any]) -> str:
    items = details.get('genres') or []
    names = [g.get('name', '').strip() for g in items if isinstance(g, dict)]
    return ', '.join(n for n in names if n)


def _countries_from_details(details: dict[str, Any]) -> str:
    items = details.get('production_countries') or []
    names = [c.get('name', '').strip() for c in items if isinstance(c, dict)]
    return ', '.join(n for n in names if n)


def _director_from_details(details: dict[str, Any]) -> str:
    crew = (details.get('credits') or {}).get('crew') or []
    directors = [c.get('name', '').strip() for c in crew if isinstance(c, dict) and c.get('job') == 'Director']
    return ', '.join(n for n in directors if n)


def _cast_from_details(details: dict[str, Any], limit: int = _CAST_LIMIT) -> str:
    cast = (details.get('credits') or {}).get('cast') or []
    names = [c.get('name', '').strip() for c in cast[:limit] if isinstance(c, dict)]
    return ', '.join(n for n in names if n)


def _seasons_line_from_details(details: dict[str, Any]) -> str | None:
    """Return `📺 Сезонов: N, серий: M` for tv shows, or None for movies / when absent."""
    seasons = details.get('number_of_seasons')
    if not isinstance(seasons, int) or seasons <= 0:
        return None
    episodes = details.get('number_of_episodes')
    if isinstance(episodes, int) and episodes > 0:
        return f'📺 Сезонов: {seasons}, серий: {episodes}'
    return f'📺 Сезонов: {seasons}'


def build_tmdb_caption(  # noqa: PLR0912 - composes a single multi-section caption; splitting reduces clarity
    name: str,
    year: int | None,
    original_title: str | None,
    details: dict[str, Any] | None,
    *,
    kp_rating: float | None = None,
    fallback_tmdb_rating: str | float | None = None,
    fallback_genres: str | None = None,
    fallback_country: str | None = None,
) -> str:
    """Build the canonical film caption from TMDB details (or partial search data).

    `details` may be either a /movie/{id} or /tv/{id} response (with optional
    `credits` appended) OR a single result dict from /search/multi — extractors
    treat both shapes the same and degrade gracefully on missing keys.

    Used by:
      - `_build_film_caption` (Film row + TMDB details, library/notification path)
      - `discovery.handlers` per-pick card (TMDB details only)
    """
    details = details or {}
    lines: list[str] = []

    safe_name = html.escape(name)
    year_part = f' ({year})' if year else ''
    lines.append(f'🎬 <b>{safe_name}</b>{year_part}')
    detail_original = (details.get('original_title') or details.get('original_name') or '').strip()
    chosen_original = detail_original or (original_title or '').strip()
    if chosen_original and chosen_original != name:
        lines.append(f'🌍 <i>{html.escape(chosen_original)}</i>')

    rating_bits: list[str] = []
    tmdb_rating = _parse_rating(details.get('vote_average'))
    if tmdb_rating is None:
        tmdb_rating = _parse_rating(fallback_tmdb_rating)
    if tmdb_rating is not None:
        rating_bits.append(f'⭐ TMDB {tmdb_rating:.1f}/10')
    if kp_rating is not None:
        rating_bits.append(f'⭐ Кинопоиск {kp_rating:.1f}/10')
    if rating_bits:
        lines.append(' | '.join(rating_bits))

    genres = _genres_from_details(details) or (fallback_genres or '').strip()
    if genres:
        lines.append(f'📁 Жанр: {html.escape(genres)}')

    country = _countries_from_details(details) or (fallback_country or '').strip()
    if country:
        lines.append(f'🌍 Страна: {html.escape(country)}')

    runtime_str = _format_runtime(_runtime_from_details(details))
    if runtime_str:
        lines.append(f'⏱ Продолжительность: {runtime_str}')

    seasons_line = _seasons_line_from_details(details)
    if seasons_line:
        lines.append(seasons_line)

    # Description before cast/crew so it always survives the 1000-char caption budget.
    overview = (details.get('overview') or '').strip()
    if overview:
        if len(overview) > 400:
            overview = overview[:397] + '…'
        lines.append('')
        lines.append(html.escape(overview))
        lines.append('')

    director = _director_from_details(details)
    if director:
        lines.append(f'🎭 Режиссёр: {html.escape(director)}')

    cast = _cast_from_details(details)
    if cast:
        lines.append(f'👥 В ролях: {html.escape(cast)}')

    return '\n'.join(lines)


def _build_film_caption(film: Film, details: dict[str, Any] | None = None) -> str:
    """Wrapper over `build_tmdb_caption` that pulls fallbacks from the Film row."""
    return build_tmdb_caption(
        name=film.name,
        year=film.year,
        original_title=film.original_title,
        details=details,
        kp_rating=film.kp_rating,
        fallback_tmdb_rating=film.rating,
        fallback_genres=film.genres,
        fallback_country=film.country,
    )


async def _format_film_card(session: AsyncSession, film: Film, torrents: list[Torrent]) -> list[Notification]:
    """Render a film as two messages: poster + TMDB info, then the releases list.

    Splitting frees us from the 1024-char photo-caption budget: the full TMDB blurb
    fits in the first message, and the torrents list (HTML links + numbered download
    buttons) lives in a second text message with the much larger 4096-char budget.

    Rutor torrent page is touched only when the Film row has no poster — the fetched
    URL gets persisted via `update_film_metadata` so subsequent cards skip the round-trip.
    """
    details = await _fetch_tmdb_details(film)

    poster_bytes: bytes | None = None
    if torrents and not film.poster:
        try:
            _info, poster_bytes, _images, fetched_poster_url, _meta = await get_torrent_info(torrents[0].link)
            if fetched_poster_url:
                await update_film_metadata(session, film.id, poster=fetched_poster_url)
        except (OSError, ValueError) as e:
            log.debug('Rutor poster enrichment failed: %s', e)

    caption = _build_film_caption(film, details)
    if len(caption) > 1000:
        caption = caption[:997] + '…'

    # Prefer TMDB poster path when present — cleaner than the rutor mirror.
    tmdb_poster = details.get('poster_path')
    tmdb_poster_url = f'https://image.tmdb.org/t/p/w500{tmdb_poster}' if tmdb_poster else None
    media: bytes | str | None = poster_bytes or tmdb_poster_url or film.poster
    has_media = bool(media)

    notifications: list[Notification] = [
        {
            'type': 'photo' if has_media else 'text',
            'media': media if has_media else None,
            'caption': caption,
            'reply_markup': None,
        }
    ]

    if torrents:
        torrents_block = _format_torrents_lines(torrents, film)
        if len(torrents_block) > 4000:
            torrents_block = torrents_block[:3997] + '…'
        notifications.append(
            {
                'type': 'text',
                'media': None,
                'caption': torrents_block,
                'reply_markup': _format_torrents_buttons(torrents, film),
            }
        )

    return notifications


def _parse_rating(value: str | float | None) -> float | None:
    """Parse Film.rating (stored as string) into a float; tolerate empty / non-numeric."""
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


async def format_films(films: Iterable[Film]) -> list[Notification]:
    """Format films for telegram messages, returns list of notification objects"""
    notifications: list[Notification] = []

    async with get_async_session() as session:
        for film in films:
            torrents = await get_torrents_by_film(session, film.id)
            if not torrents:
                continue

            notifications.extend(await _format_film_card(session, film, torrents))

    return notifications


def _episode_label_for_torrent(torrent: Torrent) -> str:
    """Build a human-readable episode label from torrent fields."""
    if torrent.season is None:
        return ''
    info = EpisodeInfo(
        season=torrent.season,
        episode=torrent.episode,
        episode_end=None,
        is_full_season=torrent.episode is None,
    )
    return format_episode_label(info)


async def format_series_notifications(films_torrents: dict[int, list[Torrent]]) -> list[Notification]:
    """Format series episode notifications showing only new episode torrents."""
    notifications: list[Notification] = []

    async with get_async_session() as session:
        film_ids = list(films_torrents.keys())
        films = await get_films_by_ids(session, film_ids)
        films_by_id = {f.id: f for f in films}

        for film_id, torrents in films_torrents.items():
            film = films_by_id.get(film_id)
            if not film:
                continue

            # Build episode summary line
            episode_labels = []
            for t in torrents:
                label = _episode_label_for_torrent(t)
                if label and label not in episode_labels:
                    episode_labels.append(label)

            safe_name = html.escape(film.name)
            ep_summary = ', '.join(episode_labels) if episode_labels else 'new episodes'
            caption = f'📺 <b>{safe_name}</b> ({film.year})\n🆕 {ep_summary}'

            if len(caption) > 1000:
                caption = caption[:997] + '...'

            markup = _format_torrents_buttons(torrents, film)
            notifications.append(
                {
                    'type': 'text',
                    'media': None,
                    'caption': caption,
                    'reply_markup': markup,
                }
            )

    return notifications
