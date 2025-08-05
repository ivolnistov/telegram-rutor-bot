"""Security decorators for telegram bot handlers"""

__all__ = ('security',)

from collections.abc import Callable
from functools import wraps
from typing import Protocol

from telegram import Update
from telegram.ext import ContextTypes

from telegram_rutor_bot.config import settings


class HandlerFunc(Protocol):
    """Protocol for telegram bot handler functions"""

    async def __call__(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: ...


def security(white_list: list[int]) -> Callable[[HandlerFunc], HandlerFunc]:
    """Decorator to check if user is in whitelist before executing handler"""

    def decorator(fn: HandlerFunc) -> HandlerFunc:
        @wraps(fn)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            msg = getattr(update, 'message', None)
            if not msg:
                return None
            user = msg.from_user
            if user and user.id not in white_list:
                if update.effective_chat:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=settings.unauthorized_message)
                return None
            return await fn(update, context)

        return wrapper

    return decorator
