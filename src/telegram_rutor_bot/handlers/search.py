"""Search-related Telegram bot command handlers"""

import contextlib
import html

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from telegram_rutor_bot.db import (
    add_search_to_db,
    delete_search,
    get_async_session,
    get_or_create_user_by_chat_id,
    get_search,
    get_searches,
    get_subscriptions,
    get_user_by_chat,
)
from telegram_rutor_bot.db import (
    subscribe as db_subscribe,
)
from telegram_rutor_bot.db import (
    unsubscribe as db_unsubscribe,
)
from telegram_rutor_bot.tasks.jobs import execute_search
from telegram_rutor_bot.utils import DEFAULT_LANGUAGE, get_cron_description, get_text, security

__all__ = (
    'search_add',
    'search_callback_handler',
    'search_delete',
    'search_execute',
    'search_list',
)


async def _get_lang(update: Update) -> str:
    chat_id = update.effective_chat.id if update.effective_chat else 0
    if not chat_id:
        return DEFAULT_LANGUAGE
    async with get_async_session() as session:
        user = await get_user_by_chat(session, chat_id)
        return user.language if user else DEFAULT_LANGUAGE


@security()
async def search_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all searches for the user"""
    assert update.effective_chat is not None  # Checked by security decorator
    lang = await _get_lang(update)

    async with get_async_session() as session:
        searches = await get_searches(session, show_empty=True)
        user = await get_user_by_chat(session, update.effective_chat.id)
        subscribed_ids = set()
        if user:
            subs = await get_subscriptions(session, user.id)
            subscribed_ids = {s.id for s in subs}

    if not searches:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('no_searches', lang))
        return

    for search in searches:
        title = search.query if search.query else f'Search #{search.id}'
        cron_desc = get_cron_description(search.cron, lang)

        # Escape title to prevent HTML injection errors
        safe_title = html.escape(title)

        text = f'🔍 <b>{safe_title}</b>\n🕒 {cron_desc}'

        buttons = []
        # Link Button
        buttons.append([InlineKeyboardButton('🔗 Rutor Link', url=search.url)])

        is_subscribed = search.id in subscribed_ids
        sub_text = '🔕 Unsubscribe' if is_subscribed else '🔔 Subscribe'
        sub_data = f'unsub_{search.id}' if is_subscribed else f'sub_{search.id}'

        # Action Buttons
        buttons.append(
            [
                InlineKeyboardButton('▶️ Run', callback_data=f'es_{search.id}'),
                InlineKeyboardButton(sub_text, callback_data=sub_data),
            ]
        )
        buttons.append([InlineKeyboardButton('🗑️ Delete', callback_data=f'ds_{search.id}')])

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode='HTML',
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(buttons),
        )


@security()
async def search_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle search-related callbacks"""
    query = update.callback_query
    if not query or not query.data:
        return

    # Ensure we have a chat context
    if not update.effective_chat:
        return

    await query.answer()

    lang = await _get_lang(update)
    data = query.data

    if data.startswith('ds_'):
        search_id = int(data.replace('ds_', ''))
        async with get_async_session() as session:
            await delete_search(session, search_id)

        # Delete the message after deleting search
        with contextlib.suppress(Exception):
            await query.delete_message()

        await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('search_deleted', lang))

    elif data.startswith('es_'):
        search_id = int(data.replace('es_', ''))
        async with get_async_session() as session:
            search = await get_search(session, search_id)

        if search:
            await execute_search.kiq(search.id, update.effective_chat.id)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'🔄 Search #{search_id} scheduled')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Search #{search_id} not found')

    elif data.startswith('sub_'):
        search_id = int(data.replace('sub_', ''))
        async with get_async_session() as session:
            success, _message = await db_subscribe(session, search_id, update.effective_chat.id)

        if success:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=get_text('subscribed', lang, search_id=search_id)
            )
    elif data.startswith('unsub_'):
        search_id = int(data.replace('unsub_', ''))
        async with get_async_session() as session:
            user = await get_user_by_chat(session, update.effective_chat.id)
            if user:
                await db_unsubscribe(session, search_id, user.id)
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text=get_text('unsubscribed', lang, search_id=search_id)
                )


@security()
async def search_execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute a search immediately"""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text

    # We don't really use lang here for log/admin messages usually, but let's be consistent if we add user feedback
    # Actually this command sends feedback to user
    search_id = int(update.message.text.replace('/es_', ''))

    async with get_async_session() as session:
        search = await get_search(session, search_id)

    if search:
        await execute_search.kiq(search.id, update.effective_chat.id)
        # Note: Providing feedback is good.
        # But existing code: "Search with id {search_id} scheduled..."
        # We can keep it simple or i18n it. The prompt didn't ask for *every* admin string but likely user-facing.
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'🔄 Search #{search_id} scheduled')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Search #{search_id} not found')


@security()
async def search_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a search by ID"""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text

    lang = await _get_lang(update)
    search_id = int(update.message.text.replace('/ds_', ''))

    async with get_async_session() as session:
        await delete_search(session, search_id)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('search_deleted', lang))


@security()
async def search_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new search"""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text

    lang = await _get_lang(update)

    # Remove command from text
    text = update.message.text
    if text.startswith('/add_search '):
        text = text[12:]  # Remove '/add_search '
    elif text == '/add_search':
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=get_text('usage_add_search', lang), disable_web_page_preview=True
        )
        return

    # Split into URL and cron parts
    parts = text.split()
    if len(parts) < 6:  # URL + 5 cron fields
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=get_text('invalid_format', lang), disable_web_page_preview=True
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
        text=get_text('search_added', lang, search_id=search_id),
    )
