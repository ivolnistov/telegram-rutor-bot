"""Torrent-related Telegram bot command handlers"""

# noinspection PyUnusedLocal
import contextlib
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import get_async_session, get_films, get_torrent_by_id
from telegram_rutor_bot.helpers import format_films
from telegram_rutor_bot.rutor import download_torrent, get_torrent_info
from telegram_rutor_bot.utils import security

__all__ = (
    'torrent_download',
    'torrent_info',
    'torrent_list',
    'torrent_search',
)


@security(settings.users_white_list)  # type: ignore[arg-type]
async def torrent_download(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dl_XXX command to download a torrent"""
    assert update.message is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text
    torrent_id = int(update.message.text.replace('/dl_', ''))
    async with get_async_session() as session:
        torrent = await get_torrent_by_id(session, torrent_id)
    if torrent:
        await download_torrent(torrent)
        await update.message.reply_text(f'Start downloading of {torrent.name}', parse_mode='Markdown')
    else:
        await update.message.reply_text('Torrent not found')


@security(settings.users_white_list)  # type: ignore[arg-type]
async def torrent_info(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Show detailed torrent information"""
    assert update.message is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text
    torrent_id = int(update.message.text.replace('/in_', ''))

    # Send initial message
    await update.message.reply_text('🔍 Getting movie information...')

    async with get_async_session() as session:
        torrent = await get_torrent_by_id(session, torrent_id)
    if not torrent:
        await update.message.reply_text('Torrent not found')
        return

    try:
        message, poster, _images = await get_torrent_info(torrent.link, f'/dl_{torrent_id}')

        # Send poster first if available
        if poster:
            await update.message.reply_photo(poster, caption=f'🎬 {torrent.name}')

        # Send main message with movie info
        await update.message.reply_text(message, disable_web_page_preview=True)
    except (OSError, ValueError) as e:
        error_msg = f'❌ Error getting information:\n{e!s}'
        await update.message.reply_text(error_msg)


@security(settings.users_white_list)
async def torrent_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List recent torrents"""
    assert update.effective_chat is not None  # Checked by security decorator
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Fetching torrents...')

        async with get_async_session() as session:
            films = await get_films(session, limit=20)

        if not films:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='No films found in database')
            return

        messages, posters = await format_films(films)

        if not messages:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='No messages to send')
            return

        # Send posters first if available
        for poster_data, caption in posters:
            with contextlib.suppress(Exception):
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=poster_data, caption=caption)

        for msg in messages:
            if msg:  # Only send non-empty messages
                await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode=None)
    except (OSError, ValueError) as e:
        error_msg = f'Error in torrent_list: {e!s}\n\n{traceback.format_exc()}'
        await context.bot.send_message(chat_id=update.effective_chat.id, text=error_msg[:4000])


@security(settings.users_white_list)
async def torrent_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for torrents"""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text
    search = str.strip(update.message.text.replace('/search', ''))
    async with get_async_session() as session:
        films = await get_films(session, limit=20, query=f"LOWER(name) LIKE LOWER('%{search}%')")
    messages, posters = await format_films(films)

    # Send posters first if available
    for poster_data, caption in posters:
        with contextlib.suppress(Exception):
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=poster_data, caption=caption)

    for msg in messages:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode=None)
