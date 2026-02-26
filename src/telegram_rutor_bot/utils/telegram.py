"""Telegram-related utilities"""

import contextlib
import logging

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from telegram_rutor_bot.schemas import Notification

log = logging.getLogger(__name__)


async def send_notifications(
    bot: Bot,
    chat_id: int,
    notifications: list[Notification],
) -> None:
    """Send a list of notifications to a specific chat_id"""
    for note in notifications:
        with contextlib.suppress(Exception):
            try:
                if note['type'] == 'photo' and note['media']:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=note['media'],
                        caption=note['caption'],
                        parse_mode=ParseMode.HTML,
                        reply_markup=note['reply_markup'],
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=note['caption'],
                        parse_mode=ParseMode.HTML,
                        reply_markup=note['reply_markup'],
                    )
            except TelegramError as e:
                log.error('Failed to send notification to %s: %s', chat_id, e)
