"""Force-reply flow for commands that need an argument.

Telegram's command picker sends bare commands such as `/search`. For commands
that need text, we ask via ForceReply and then dispatch the reply back to the
original handler with synthetic command text.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from telegram import ForceReply, Update
from telegram.ext import ContextTypes

from telegram_rutor_bot.utils import DEFAULT_LANGUAGE

log = logging.getLogger(__name__)

_PENDING_KEY = 'pending_command'

_PROMPTS: dict[str, tuple[str, str]] = {
    'search': ('What to search?', 'Что искать?'),
    'watch': ('Movie or show name?', 'Название фильма или сериала?'),
    'adduser': ('New user chat ID?', 'Chat ID нового пользователя?'),
    'discovery': ('Title to look up on TMDB?', 'Название для поиска на TMDB?'),
}

type HandlerCallable = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]
_HANDLERS: dict[str, HandlerCallable] = {}


def register_pending_handler(command: str, handler: HandlerCallable) -> None:
    """Register a command handler that can receive a ForceReply argument."""
    _HANDLERS[command] = handler


async def request_arg(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    command: str,
    lang: str = DEFAULT_LANGUAGE,
) -> None:
    """Ask the user for the missing argument via ForceReply."""
    if update.message is None:
        return
    en_prompt, ru_prompt = _PROMPTS.get(command, ('Argument?', 'Аргумент?'))
    prompt = ru_prompt if (lang or '').startswith('ru') else en_prompt

    if context.user_data is not None:
        context.user_data[_PENDING_KEY] = command

    await update.message.reply_text(
        prompt,
        reply_markup=ForceReply(input_field_placeholder=prompt[:64], selective=True),
    )


async def handle_pending_arg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Re-dispatch a ForceReply answer to the original command handler."""
    if update.message is None or update.message.text is None:
        return
    pending = (context.user_data or {}).pop(_PENDING_KEY, None)
    if not pending:
        return
    handler = _HANDLERS.get(pending)
    if handler is None:
        log.warning('No handler registered for pending command %r', pending)
        return

    arg_text = update.message.text
    forged = f'/{pending} {arg_text}' if arg_text else f'/{pending}'
    msg: Any = update.message
    try:
        msg._unfreeze()  # pylint: disable=protected-access
        msg.text = forged
    except (AttributeError, RuntimeError) as exc:
        log.debug('Could not synthesise /%s text on Message: %s', pending, exc)

    await handler(update, context)
