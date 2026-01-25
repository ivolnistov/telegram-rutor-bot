"""Torrent-related Telegram bot command handlers"""

# noinspection PyUnusedLocal
import contextlib
import html
import re
import traceback
from typing import Any
from urllib.parse import urljoin

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from telegram_rutor_bot.db import (
    get_async_session,
    get_films,
    get_recommendations,
    get_torrent_by_id,
    get_user_by_chat,
)
from telegram_rutor_bot.helpers import format_films
from telegram_rutor_bot.rutor import download_torrent, get_torrent_info
from telegram_rutor_bot.rutor.rating_parser import get_imdb_details
from telegram_rutor_bot.torrent_clients import get_torrent_client
from telegram_rutor_bot.utils import DEFAULT_LANGUAGE, get_text, security

__all__ = (
    'callback_query_handler',
    'download_torrent',
    'torrent_download',
    'torrent_downloads',
    'torrent_info',
    'torrent_list',
    'torrent_recommend',
    'torrent_search',
)


async def _get_lang(update: Update) -> str:
    chat_id = update.effective_chat.id if update.effective_chat else 0
    if not chat_id:
        return DEFAULT_LANGUAGE
    async with get_async_session() as session:
        user = await get_user_by_chat(session, chat_id)
        return user.language if user else DEFAULT_LANGUAGE


@security()
async def torrent_download(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dl_XXX command to download a torrent"""
    assert update.message is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text

    lang = await _get_lang(update)
    torrent_id = int(update.message.text.replace('/dl_', ''))

    async with get_async_session() as session:
        torrent = await get_torrent_by_id(session, torrent_id)

    if torrent:
        await download_torrent(torrent)
        safe_name = html.escape(torrent.name)
        await update.message.reply_text(get_text('start_downloading', lang, name=safe_name), parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(get_text('torrent_not_found', lang))


@security()
async def torrent_info(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed torrent information"""
    assert update.message is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text

    lang = await _get_lang(update)
    torrent_id = int(update.message.text.replace('/in_', ''))

    # Send initial message
    await update.message.reply_text(get_text('getting_info', lang))

    async with get_async_session() as session:
        torrent = await get_torrent_by_id(session, torrent_id)

    if not torrent:
        await update.message.reply_text(get_text('torrent_not_found', lang))
        return

    try:
        # Note: formatting here is still old-style text based, but at least we escape title in caption
        message, poster, _images, poster_url, metadata = await get_torrent_info(torrent.link)

        safe_name = html.escape(torrent.name)
        # Send poster first if available
        media = poster or poster_url
        if media:
            await update.message.reply_photo(media, caption=f'🎬 <b>{safe_name}</b>', parse_mode=ParseMode.HTML)

        # Construct buttons
        buttons = []
        # Download button
        buttons.append([InlineKeyboardButton('⬇️ Download', callback_data=f'dl_{torrent_id}')])

        # Link buttons
        links_row = []
        rutor_url = urljoin('http://rutor.info', torrent.link)
        links_row.append(InlineKeyboardButton('🔗 Rutor', url=rutor_url))

        if metadata.get('imdb_url'):
            links_row.append(InlineKeyboardButton('⭐ IMDB', url=metadata['imdb_url']))
        if metadata.get('kp_url'):
            links_row.append(InlineKeyboardButton('🎬 KP', url=metadata['kp_url']))

        if links_row:
            buttons.append(links_row)

        reply_markup = InlineKeyboardMarkup(buttons)

        # Send main message with movie info
        await update.message.reply_text(message, disable_web_page_preview=True, reply_markup=reply_markup)
    except (OSError, ValueError) as e:
        error_msg = get_text('error_getting_info', lang, error=str(e))
        await update.message.reply_text(error_msg)


@security()
async def torrent_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List recent torrents"""
    assert update.effective_chat is not None  # Checked by security decorator

    lang = await _get_lang(update)

    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('fetching_torrents', lang))

        async with get_async_session() as session:
            films = await get_films(session, limit=20)

        if not films:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('no_films_db', lang))
            return

        notifications = await format_films(films)

        if not notifications:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('no_messages', lang))
            return

        for note in notifications:
            with contextlib.suppress(Exception):
                if note['type'] == 'photo' and note['media']:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=note['media'],
                        caption=note['caption'],
                        parse_mode=ParseMode.HTML,
                        reply_markup=note['reply_markup'],
                    )
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=note['caption'],  # caption field holds text for text-only messages
                        parse_mode=ParseMode.HTML,
                        reply_markup=note['reply_markup'],
                    )

    except (OSError, ValueError) as e:
        error_msg = f'Error in torrent_list: {e!s}\n\n{traceback.format_exc()}'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=error_msg[:4000])


@security()
async def torrent_downloads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List active downloads with management buttons"""
    assert update.effective_chat is not None

    try:
        client = get_torrent_client()
        await client.connect()
        try:
            torrents = await client.list_torrents()
        finally:
            await client.disconnect()
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Error connecting to client: {e}')
        return

    if not torrents:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='No active downloads.')
        return

    for torrent in torrents:
        # Format status line
        status_icon = '🟢' if torrent['status'] in ['downloading', 'seeding', 'stalleddl'] else '🟠'
        if torrent['status'] in ['pauseddl', 'pausedup']:
            status_icon = '⏸️'
        elif torrent['status'] in ['error', 'missingfiles']:
            status_icon = '🔴'

        progress = f'{torrent["progress"]:.1f}%'
        # 1024**3 = 1073741824 (GiB)
        size_gb = torrent['size'] / 1073741824

        caption = (
            f'{status_icon} <b>{html.escape(torrent["name"])}</b>\n'
            f'State: {torrent["status"]}\n'
            f'Progress: {progress} • Size: {size_gb:.2f} GB\n'
            f'▼ {torrent["download_rate"] / 1024:.1f} KiB/s • ▲ {torrent["upload_rate"] / 1024:.1f} KiB/s'
        )

        buttons = []
        # Management buttons
        row = []
        if torrent['status'] in ['pauseddl', 'pausedup']:
            row.append(InlineKeyboardButton('▶️ Resume', callback_data=f'resume_{torrent["hash"]}'))
        else:
            row.append(InlineKeyboardButton('⏸️ Pause', callback_data=f'pause_{torrent["hash"]}'))

        row.append(InlineKeyboardButton('🗑️ Delete', callback_data=f'delete_{torrent["hash"]}'))
        buttons.append(row)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
        )


@security()
async def torrent_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for torrents"""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text

    lang = await _get_lang(update)
    search = str.strip(update.message.text.replace('/search', ''))

    # Check for IMDB ID/URL
    if 'imdb.com' in search or search.startswith('tt'):
        await _handle_imdb_search(update, context, search, lang)
        return

    await _handle_text_search(update, context, search, lang)


async def _handle_imdb_search(update: Update, context: ContextTypes.DEFAULT_TYPE, search: str, lang: str) -> None:
    """Handle search by IMDB ID/URL"""
    assert update.effective_chat is not None
    await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('fetching_info', lang))

    # Extract ID if it's a URL
    imdb_id = search
    if 'imdb.com' in search:
        match = re.search(r'(tt\d+)', search)
        if match:
            imdb_id = match.group(1)

    details = await get_imdb_details(imdb_id)
    if details:
        await _send_imdb_info(update, context, details)
        return

    await context.bot.send_message(chat_id=update.effective_chat.id, text='IMDB info not found')


async def _send_imdb_info(update: Update, context: ContextTypes.DEFAULT_TYPE, details: dict[str, Any]) -> None:
    """Send IMDB movie info"""
    assert update.effective_chat is not None
    caption_parts = []
    if details.get('title'):
        title = html.escape(details['title'])
        if details.get('year'):
            title += f' ({details["year"]})'
        caption_parts.append(f'🎬 <b>{title}</b>')

    if details.get('rating'):
        caption_parts.append(f'⭐ IMDB: {details["rating"]}/10')

    if details.get('genres'):
        caption_parts.append(f'📁 {details["genres"]}')

    if details.get('description'):
        caption_parts.append(f'\n📝 {details["description"]}')

    caption = '\n'.join(caption_parts)

    buttons = []
    if details.get('title'):
        # Search button using title
        search_query = details['title']
        buttons.append([InlineKeyboardButton('🔍 Search on Rutor', switch_inline_query_current_chat=search_query)])

    reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

    if details.get('poster_url'):
        with contextlib.suppress(Exception):
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=details['poster_url'],
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
            )
            return

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup
    )


async def _handle_text_search(update: Update, context: ContextTypes.DEFAULT_TYPE, search: str, lang: str) -> None:
    """Handle standard text search"""
    assert update.effective_chat is not None
    async with get_async_session() as session:
        films = await get_films(session, limit=20, query=f"LOWER(f.name) LIKE LOWER('%{search}%')")

    notifications = await format_films(films)

    if not notifications:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('no_films_found', lang))
        return

    for note in notifications:
        with contextlib.suppress(Exception):
            if note['type'] == 'photo' and note['media']:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=note['media'],
                    caption=note['caption'],
                    parse_mode=ParseMode.HTML,
                    reply_markup=note['reply_markup'],
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=note['caption'],
                    parse_mode=ParseMode.HTML,
                    reply_markup=note['reply_markup'],
                )


@security()
async def torrent_recommend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recommend films based on user history"""
    assert update.effective_chat is not None

    lang = await _get_lang(update)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('fetching_info', lang))

    async with get_async_session() as session:
        recommendations = await get_recommendations(session, limit=5)

    if not recommendations:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text='No recommendations found. Try downloading simpler genres first!'
        )
        return

    notifications = await format_films(recommendations)

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text='🎬 <b>Recommended for you:</b>', parse_mode=ParseMode.HTML
    )

    for note in notifications:
        with contextlib.suppress(Exception):
            if note['type'] == 'photo' and note['media']:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=note['media'],
                    caption=note['caption'],
                    parse_mode=ParseMode.HTML,
                    reply_markup=note['reply_markup'],
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=note['caption'],
                    parse_mode=ParseMode.HTML,
                    reply_markup=note['reply_markup'],
                )


@security()
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if not query.data:
        return

    lang = await _get_lang(update)

    if query.data.startswith('dl_'):
        torrent_id = int(query.data.replace('dl_', ''))
        async with get_async_session() as session:
            torrent = await get_torrent_by_id(session, torrent_id)

        if torrent:
            await download_torrent(torrent)
            # Remove buttons or keep? Usually better to keep but we can remove if we want single-use.
            # Keeping buttons allows downloading again if needed.

            safe_name = html.escape(torrent.name)
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=get_text('started_downloading', lang, name=safe_name),
                    parse_mode=ParseMode.HTML,
                )
        elif update.effective_chat:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('torrent_not_found', lang))
            return

    # Handle management actions
    action = None
    torrent_hash = None

    if query.data.startswith('pause_'):
        action = 'pause'
        torrent_hash = query.data.replace('pause_', '')
    elif query.data.startswith('resume_'):
        action = 'resume'
        torrent_hash = query.data.replace('resume_', '')
    elif query.data.startswith('delete_'):
        action = 'delete'
        torrent_hash = query.data.replace('delete_', '')

    if action and torrent_hash:
        await _handle_management_action(query, update, action, torrent_hash)


async def _handle_management_action(query: CallbackQuery, update: Update, action: str, torrent_hash: str) -> None:
    """Helper to handle torrent management actions"""
    try:
        client = get_torrent_client()
        await client.connect()
        try:
            if not query.message or not isinstance(query.message, Message):
                return

            current_caption = query.message.caption or ''
            if action == 'pause':
                await client.pause_torrent(torrent_hash)
                await query.edit_message_caption(caption=f'{current_caption}\n\n✅ Paused')
            elif action == 'resume':
                await client.resume_torrent(torrent_hash)
                await query.edit_message_caption(caption=f'{current_caption}\n\n✅ Resumed')
            elif action == 'delete':
                await client.remove_torrent(torrent_hash, delete_files=True)
                await query.edit_message_text(text=f'🗑️ Deleted: {torrent_hash}')
        finally:
            await client.disconnect()
    except Exception as e:
        if update.effective_chat:
            # Use context.bot if available or query.get_bot()
            # Casting or ignoring for now as bot is usually present
            bot = query.get_bot()
            await bot.send_message(chat_id=update.effective_chat.id, text=f'Error: {e}')
