"""Subscription-related Telegram bot command handlers"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_rutor_bot.db import (
    get_async_session,
    get_subscriptions,
    get_user_by_chat,
)
from telegram_rutor_bot.db import (
    subscribe as db_subscribe,
)
from telegram_rutor_bot.db import (
    unsubscribe as db_unsubscribe,
)
from telegram_rutor_bot.utils import DEFAULT_LANGUAGE, get_text, security

__all__ = (
    'subscribe',
    'subscriptions_list',
    'unsubscribe',
)


async def _get_lang(update: Update) -> str:
    chat_id = update.effective_chat.id if update.effective_chat else 0
    if not chat_id:
        return DEFAULT_LANGUAGE
    async with get_async_session() as session:
        user = await get_user_by_chat(session, chat_id)
        return user.language if user else DEFAULT_LANGUAGE


@security()
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to search notifications."""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text

    lang = await _get_lang(update)
    search_id = int(update.message.text.replace('/subscribe_', ''))

    async with get_async_session() as session:
        # Note: db_subscribe returns English strings.
        # Ideally we should refactor db_subscribe to return codes, but for now we trust it or show it.
        # However, for success we use our localized string.
        success, message = await db_subscribe(session, search_id, update.effective_chat.id)

    if not success:
        # Try to localize common errors
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=get_text('subscribed', lang, search_id=search_id)
    )


@security()
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from search notifications."""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text

    lang = await _get_lang(update)
    search_id = int(update.message.text.replace('/unsubscribe_', ''))

    async with get_async_session() as session:
        user = await get_user_by_chat(session, update.effective_chat.id)
        if user:
            await db_unsubscribe(session, search_id, user.id)

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=get_text('unsubscribed', lang, search_id=search_id)
    )


@security()
async def subscriptions_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all user subscriptions."""
    assert update.effective_chat is not None  # Checked by security decorator

    lang = await _get_lang(update)

    async with get_async_session() as session:
        user = await get_user_by_chat(session, update.effective_chat.id)
        if not user:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=get_text('no_subscriptions', lang))
            return

        message = ''
        subscriptions = await get_subscriptions(session, user.id)
        for search in subscriptions:
            message += f'/ds_{search.id} {search.url}\n'

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message or get_text('no_subscriptions', lang))
