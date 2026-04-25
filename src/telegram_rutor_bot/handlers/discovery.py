"""Discovery (TMDB) Telegram bot command handlers"""

import asyncio
import contextlib
import html
import logging
from typing import Any

from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram import error as telegram_error
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from telegram_rutor_bot.clients.tmdb import TmdbClient
from telegram_rutor_bot.db import (
    get_async_session,
    get_or_create_film,
    get_torrents_by_film,
    get_user_by_chat,
    update_film_metadata,
)
from telegram_rutor_bot.db.models import Film
from telegram_rutor_bot.helpers import build_tmdb_caption, format_films
from telegram_rutor_bot.tasks.jobs import search_film_on_rutor
from telegram_rutor_bot.utils import DEFAULT_LANGUAGE, get_text, security, send_notifications

__all__ = (
    'discovery_callback_handler',
    'discovery_command',
    'discovery_season_callback_handler',
)

log = logging.getLogger(__name__)

_MAX_RESULTS: int = 5
_CALLBACK_PREFIX: str = 'disc_rutor:'
_SEASON_PICKER_PREFIX: str = 'disc_season:'
_SEASONS_PER_ROW: int = 4
_MAX_SEASONS_BUTTONS: int = 24  # Telegram caps inline keyboards at 100; keep it sane.

tmdb = TmdbClient()


async def _get_lang(update: Update) -> str:
    """Resolve UI language from the user record (fallback to default)."""
    chat_id = update.effective_chat.id if update.effective_chat else 0
    if not chat_id:
        return DEFAULT_LANGUAGE
    async with get_async_session() as session:
        user = await get_user_by_chat(session, chat_id)
        return user.language if user else DEFAULT_LANGUAGE


def _extract_title(item: dict[str, Any]) -> str:
    """Pick the best human-readable title from a TMDB item."""
    title = item.get('title') or item.get('name') or item.get('original_title') or item.get('original_name')
    if not title:
        return 'Unknown'
    return str(title)


def _extract_year(item: dict[str, Any]) -> int | None:
    """Extract a release/first-air year from a TMDB item, if present."""
    raw_date = item.get('release_date') or item.get('first_air_date')
    if not raw_date:
        return None
    try:
        return int(str(raw_date)[:4])
    except (ValueError, TypeError):
        return None


def _filter_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop TMDB items missing the keys we need to act on."""
    filtered: list[dict[str, Any]] = []
    for item in results:
        if not item.get('id'):
            continue
        media_type = item.get('media_type')
        if media_type not in ('movie', 'tv'):
            continue
        filtered.append(item)
    return filtered


def _parse_callback_data(data: str) -> tuple[str, int, int | None] | None:
    """Parse `disc_rutor:<media_type>:<media_id>[:<season>]`.

    Optional 3rd segment is a season number (0 = all-seasons sentinel for tv).
    Returns None on malformed input.
    """
    if not data.startswith(_CALLBACK_PREFIX):
        return None
    payload = data[len(_CALLBACK_PREFIX) :]
    parts = payload.split(':')
    if len(parts) < 2 or len(parts) > 3:
        return None
    media_type, raw_id = parts[0], parts[1]
    if not media_type or not raw_id:
        return None
    try:
        media_id = int(raw_id)
    except ValueError:
        return None
    season: int | None = None
    if len(parts) == 3:
        try:
            season_int = int(parts[2])
        except ValueError:
            return None
        season = season_int if season_int > 0 else None  # 0 = all-seasons sentinel
    return media_type, media_id, season


def _parse_season_callback_data(data: str) -> int | None:
    """Parse `disc_season:<media_id>`; only used for the season-picker entry button."""
    if not data.startswith(_SEASON_PICKER_PREFIX):
        return None
    raw = data[len(_SEASON_PICKER_PREFIX) :]
    try:
        return int(raw)
    except ValueError:
        return None


def _build_search_query(
    name: str,
    year: int | None,
    original_title: str | None,
    *,
    is_tv: bool = False,
    season: int | None = None,
) -> str:
    """Compose the rutor search string.

    Prefer the original (English/source-language) title — old foreign films are usually
    indexed on rutor under their original name; the localized name often misses releases.
    Fall back to `name` when the original is missing or identical.

    For TV we drop the year — TMDB's `first_air_date` year rarely appears in season /
    episode release names, so including it is more likely to filter out matches than help.
    A specific season (`S01`) is appended when requested by the picker.
    """
    base = (
        original_title.strip() if original_title and original_title.strip() and original_title.strip() != name else name
    )
    if season:
        return f'{base} S{season:02d}'
    if year and not is_tv:
        return f'{base} {year}'
    return base


@security()
async def discovery_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `/discovery <название>` — search TMDB and offer rutor parsing."""
    assert update.message is not None  # security() guarantees a message
    assert update.effective_chat is not None
    assert update.message.text is not None

    lang = await _get_lang(update)
    query = update.message.text.replace('/discovery', '', 1).strip()

    if not query:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('discovery_usage', lang))
        return

    try:
        raw_results = await tmdb.search_multi(query)
    except Exception as e:
        # Catching broadly here because TmdbClient internals already swallow httpx errors,
        # so a leak here usually means an unexpected client/runtime issue we want logged.
        log.exception('TMDB search_multi failed for query %r: %s', query, e)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('discovery_tmdb_error', lang))
        return

    results = _filter_results(raw_results)[:_MAX_RESULTS]
    if not results:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('discovery_no_results', lang))
        return

    # Optional header so the user sees something while detail fetches run in parallel.
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=get_text('discovery_results_header', lang),
        parse_mode=ParseMode.HTML,
    )

    # Parallel-fetch full details with credits for each pick — gives us director, cast,
    # runtime, genres list, and country names in one shot per result.
    detail_tasks = [_safe_get_details(item['media_type'], item['id']) for item in results]
    details_list = await asyncio.gather(*detail_tasks)

    for item, details in zip(results, details_list, strict=True):
        await _send_pick_card(context, update.effective_chat.id, item, details, lang)


async def _safe_get_details(media_type: str, media_id: int) -> dict[str, Any]:
    """Best-effort TMDB details fetch — empty dict on any error so the picker can degrade."""
    try:
        return await tmdb.get_details(media_type, media_id, append_to_response='credits')
    except Exception as e:
        log.debug('TMDB get_details failed for %s/%s: %s', media_type, media_id, e)
        return {}


async def _send_pick_card(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    item: dict[str, Any],
    details: dict[str, Any],
    lang: str,
) -> None:
    """Send one TMDB result as its own message — photo + caption + 'pick' button."""
    name = _extract_title({**item, **details})
    year = _extract_year({**item, **details})
    original_title = (
        details.get('original_title')
        or details.get('original_name')
        or item.get('original_title')
        or item.get('original_name')
    )

    caption = build_tmdb_caption(
        name=name,
        year=year,
        original_title=original_title,
        details=details or item,  # search_multi result is enough for a basic card if details fetch failed
    )
    if len(caption) > 1000:
        caption = caption[:997] + '…'

    media_type = item['media_type']
    media_id = int(item['id'])
    if media_type == 'tv':
        # TV: show the season picker first; lets the user narrow rutor search to one season.
        button = InlineKeyboardButton(
            get_text('btn_discovery_pick_seasons', lang),
            callback_data=f'{_SEASON_PICKER_PREFIX}{media_id}',
        )
    else:
        button = InlineKeyboardButton(
            get_text('btn_discovery_pick_torrents', lang),
            callback_data=f'{_CALLBACK_PREFIX}{media_type}:{media_id}',
        )
    markup = InlineKeyboardMarkup([[button]])

    poster_path = details.get('poster_path') or item.get('poster_path')
    poster_url = f'https://image.tmdb.org/t/p/w500{poster_path}' if poster_path else None

    if poster_url:
        with contextlib.suppress(telegram_error.TelegramError):
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=poster_url,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=markup,
            )
            return

    # Fallback to plain text when we have no poster (or send_photo failed).
    await context.bot.send_message(
        chat_id=chat_id,
        text=caption,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=markup,
    )


@security()
async def discovery_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the user's pick from `/discovery` results — kick off rutor parse."""
    callback_query = update.callback_query
    if not callback_query or not callback_query.data:
        return
    if not update.effective_chat:
        return

    lang = await _get_lang(update)
    parsed = _parse_callback_data(callback_query.data)
    if parsed is None:
        await callback_query.answer()
        return

    media_type, media_id, season = parsed
    await callback_query.answer()

    film, display_name, display_year, original_title = await _ensure_film_for_tmdb(media_type, media_id)
    if film is None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('discovery_tmdb_error', lang))
        return

    chat_id = update.effective_chat.id
    safe_title = html.escape(display_name)
    year_str = str(display_year) if display_year else '—'

    async with get_async_session() as session:
        existing_torrents = await get_torrents_by_film(session, film.id)

    # Filter DB hits to the requested season when the user picked one — the parser
    # already records `Torrent.season` from `S01E02` markers (commit 725a5f7).
    if season is not None:
        existing_torrents = [t for t in existing_torrents if (t.season or 0) == season]

    if existing_torrents:
        # DB has the film + torrents — show what we have, skip the rutor refresh.
        notifications = await format_films([film])
        await send_notifications(context.bot, chat_id, notifications)
        confirmation = get_text(
            'discovery_existing_from_db',
            lang,
            title=safe_title,
            year=year_str,
            count=len(existing_torrents),
        )
    else:
        # Nothing yet for this film/season — go to rutor and notify when the worker finishes.
        confirmation = get_text('discovery_search_started', lang, title=safe_title, year=year_str)
        search_query = _build_search_query(
            display_name,
            display_year,
            original_title,
            is_tv=(media_type == 'tv'),
            season=season,
        )
        await search_film_on_rutor.kiq(film.id, search_query, requester_chat_id=chat_id)

    # Prefer editing the picker message so the user sees their choice was registered;
    # fall back to a fresh message if Telegram refuses the edit.
    edited = False
    with contextlib.suppress(telegram_error.TelegramError):
        await callback_query.edit_message_text(text=confirmation, parse_mode=ParseMode.HTML)
        edited = True

    if not edited:
        await context.bot.send_message(chat_id=chat_id, text=confirmation, parse_mode=ParseMode.HTML)


@security()
async def discovery_season_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Replace the TV pick card's keyboard with one button per season + 'all seasons'."""
    callback_query = update.callback_query
    if not callback_query or not callback_query.data:
        return
    if not update.effective_chat:
        return

    lang = await _get_lang(update)
    media_id = _parse_season_callback_data(callback_query.data)
    if media_id is None:
        await callback_query.answer()
        return
    await callback_query.answer()

    details = await _safe_get_details('tv', media_id)
    season_numbers = _extract_season_numbers(details)

    buttons: list[list[InlineKeyboardButton]] = []
    # "All seasons" first — fast path for users who don't care about season filter.
    buttons.append(
        [
            InlineKeyboardButton(
                get_text('btn_discovery_all_seasons', lang),
                callback_data=f'{_CALLBACK_PREFIX}tv:{media_id}:0',
            )
        ]
    )

    row: list[InlineKeyboardButton] = []
    for season_n in season_numbers[:_MAX_SEASONS_BUTTONS]:
        row.append(
            InlineKeyboardButton(
                get_text('btn_discovery_season', lang, n=season_n),
                callback_data=f'{_CALLBACK_PREFIX}tv:{media_id}:{season_n}',
            )
        )
        if len(row) == _SEASONS_PER_ROW:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    markup = InlineKeyboardMarkup(buttons)

    # Edit only the keyboard so the photo + caption from the pick card stay in place.
    with contextlib.suppress(telegram_error.TelegramError):
        await callback_query.edit_message_reply_markup(reply_markup=markup)


def _extract_season_numbers(details: dict[str, Any]) -> list[int]:
    """Pull non-special season numbers from TMDB tv details (skips season 0 / Specials)."""
    seasons = details.get('seasons') or []
    numbers: list[int] = []
    for s in seasons:
        if not isinstance(s, dict):
            continue
        n = s.get('season_number')
        if isinstance(n, int) and n >= 1:
            numbers.append(n)
    if not numbers:
        # Fallback: TMDB sometimes only exposes `number_of_seasons` (e.g. degraded response)
        total = details.get('number_of_seasons')
        if isinstance(total, int) and total >= 1:
            numbers = list(range(1, total + 1))
    return sorted(numbers)


async def _ensure_film_for_tmdb(media_type: str, media_id: int) -> tuple[Film | None, str, int | None, str | None]:
    """Look up or create a Film row for the TMDB id; return (film, name, year, original_title)."""
    async with get_async_session() as session:
        existing = (await session.execute(select(Film).where(Film.tmdb_id == media_id))).scalar_one_or_none()

        details: dict[str, Any] = {}
        try:
            details = await tmdb.get_details(media_type, media_id)
        except Exception as e:
            # TmdbClient already returns {} on httpx errors, but a transport-level
            # exception bubbling up here means we still want a row if we have one.
            log.warning('TMDB get_details failed for %s/%s: %s', media_type, media_id, e)

        details_original = details.get('original_title') or details.get('original_name')

        if existing:
            year = existing.year if existing.year else _extract_year(details)
            display_name = existing.name or _extract_title(details)
            return existing, display_name, year, existing.original_title or details_original

        if not details:
            return None, '', None, None

        name = _extract_title(details)
        year = _extract_year(details)
        original_title = details_original

        country: str | None = None
        production_countries = details.get('production_countries') or []
        if production_countries:
            first_country = production_countries[0]
            if isinstance(first_country, dict):
                country = first_country.get('name')

        rating_raw = details.get('vote_average')
        rating: float | None = None
        if rating_raw is not None:
            try:
                rating = float(rating_raw)
            except (TypeError, ValueError):
                rating = None

        dummy_blake = f'tmdb_{media_type}_{media_id}'
        film = await get_or_create_film(
            session,
            blake=dummy_blake,
            year=year,
            name=name,
            poster=details.get('poster_path'),
            rating=rating,
            original_title=original_title,
            country=country,
        )
        await update_film_metadata(
            session,
            film_id=film.id,
            tmdb_id=media_id,
            tmdb_media_type=media_type,
            year=year,
            name=name,
            poster=details.get('poster_path'),
            rating=rating,
            original_title=original_title,
            country=country,
        )
        return film, name, year, original_title
