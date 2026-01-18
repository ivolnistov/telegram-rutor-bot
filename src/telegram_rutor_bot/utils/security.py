"""Security decorators for telegram bot handlers"""

__all__ = ('security',)

from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import get_async_session
from telegram_rutor_bot.db.users import get_or_create_user_by_chat_id

HandlerFunc = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]


def security() -> Callable[[HandlerFunc], HandlerFunc]:
    """Decorator to check if user is authorized in DB before executing handler"""

    def decorator(fn: HandlerFunc) -> HandlerFunc:
        @wraps(fn)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            # Support CallbackQuery updates which also have from_user but might not have message
            user = update.effective_user

            if user:
                is_authorized = False

                async with get_async_session() as session:
                    db_user = await get_or_create_user_by_chat_id(
                        session, chat_id=user.id, name=user.full_name, username=user.username
                    )

                    if db_user.is_authorized:
                        is_authorized = True

                if not is_authorized:
                    if update.effective_chat:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id, text=settings.unauthorized_message
                        )
                    return None

            return await fn(update, context)

        return wrapper

    return decorator
