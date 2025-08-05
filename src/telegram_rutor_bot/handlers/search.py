"""Search-related Telegram bot command handlers"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import (
    add_search_to_db,
    delete_search,
    get_async_session,
    get_or_create_user_by_chat_id,
    get_search,
    get_searches,
)
from telegram_rutor_bot.tasks.jobs import execute_search
from telegram_rutor_bot.utils import security

__all__ = (
    'search_add',
    'search_delete',
    'search_execute',
    'search_list',
)


@security(settings.users_white_list)
async def search_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all searches for the user"""
    assert update.effective_chat is not None  # Checked by security decorator
    message = ''
    async with get_async_session() as session:
        searches = await get_searches(session, show_empty=True)
        for search in searches:
            message += f'ID: {search.id}\n'
            message += f'URL: {search.url}\n'
            message += f'Cron: {search.cron}\n'
            message += f'Actions: /ds_{search.id} /es_{search.id} /subscribe_{search.id}\n'
            message += '---\n'
    if not message:
        message = 'No searches defined'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


@security(settings.users_white_list)
async def search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute a search immediately"""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text
    search_id = int(update.message.text.replace('/es_', ''))
    async with get_async_session() as session:
        search = await get_search(session, search_id)
    if search:
        # Schedule the task to run asynchronously with requester's chat ID
        await execute_search.kiq(search.id, update.effective_chat.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f'🔄 Search with id {search_id} scheduled for execution'
        )
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'search with id {search_id} not found')


@security(settings.users_white_list)
async def search_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a search by ID"""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text
    search_id = int(update.message.text.replace('/ds_', ''))
    async with get_async_session() as session:
        await delete_search(session, search_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text='search was deleted')


@security(settings.users_white_list)
async def search_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new search"""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text
    # Remove command from text
    text = update.message.text
    if text.startswith('/add_search '):
        text = text[12:]  # Remove '/add_search '
    elif text == '/add_search':
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Usage: /add_search <url> <cron>\nExample: /add_search http://rutor.info/search/0/0/100/0/matrix * * * * *',
        )
        return

    # Split into URL and cron parts
    parts = text.split()
    if len(parts) < 6:  # URL + 5 cron fields
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Invalid format. Must be: /add_search <url> <minute> <hour> <day> <month> <day_of_week>\nExample: /add_search http://rutor.info/search/0/0/100/0/matrix * * * * *',
        )
        return

    search_url = parts[0]
    cron = ' '.join(parts[1:6])  # Take exactly 5 cron fields

    try:
        async with get_async_session() as session:
            user = await get_or_create_user_by_chat_id(session, update.effective_chat.id)
            search_id = await add_search_to_db(session, search_url, cron, user.id)
    except (ValueError, OSError) as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Error: {e!s}')
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'✅ Search added with ID {search_id}\n\nNow you can:\n/subscribe_{search_id} - Subscribe to notifications\n/es_{search_id} - Execute search now',
    )
