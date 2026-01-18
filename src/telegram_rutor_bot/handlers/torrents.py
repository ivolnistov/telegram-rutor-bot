"""Torrent-related Telegram bot command handlers"""

# noinspection PyUnusedLocal
import contextlib
import html
import traceback
from urllib.parse import urljoin

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from telegram_rutor_bot.db import (
    get_async_session,
    get_films,
    get_torrent_by_id,
    get_user_by_chat,
)
from telegram_rutor_bot.helpers import format_films
from telegram_rutor_bot.rutor import download_torrent, get_torrent_info
from telegram_rutor_bot.utils import DEFAULT_LANGUAGE, get_text, security

__all__ = (
    'callback_query_handler',
    'download_torrent',
    'torrent_download',
    'torrent_info',
    'torrent_list',
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
async def torrent_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for torrents"""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text

    lang = await _get_lang(update)
    search = str.strip(update.message.text.replace('/search', ''))

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
