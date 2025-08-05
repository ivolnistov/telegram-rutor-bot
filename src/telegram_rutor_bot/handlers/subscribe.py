"""Subscription-related Telegram bot command handlers"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_rutor_bot.config import settings
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
from telegram_rutor_bot.utils import security

__all__ = (
    'subscribe',
    'subscriptions_list',
    'unsubscribe',
)


@security(settings.users_white_list)
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to search notifications."""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text
    search_id = int(update.message.text.replace('/subscribe_', ''))
    async with get_async_session() as session:
        success, message = await db_subscribe(session, search_id, update.effective_chat.id)
    if not success:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'You subscribed to search {search_id}')


@security(settings.users_white_list)
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from search notifications."""
    assert update.message is not None  # Checked by security decorator
    assert update.effective_chat is not None  # Checked by security decorator
    assert update.message.text is not None  # Commands always have text
    search_id = int(update.message.text.replace('/unsubscribe_', ''))
    async with get_async_session() as session:
        user = await get_user_by_chat(session, update.effective_chat.id)
        if user:
            await db_unsubscribe(session, search_id, user.id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'You unsubscribed from search {search_id}')


@security(settings.users_white_list)
async def subscriptions_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all user subscriptions."""
    assert update.effective_chat is not None  # Checked by security decorator
    async with get_async_session() as session:
        user = await get_user_by_chat(session, update.effective_chat.id)
        if not user:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='No subscriptions')
            return

        message = ''
        subscriptions = await get_subscriptions(session, user.id)
        for search in subscriptions:
            message += f'/ds_{search.id} {search.url}\n'
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message or 'No subscriptions')
