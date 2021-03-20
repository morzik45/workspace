import logging

from aiogram import Dispatcher
from aiogram.types import ContentType

import handlers.users as users


async def register_handlers(dp: Dispatcher):
    dp.register_message_handler(users.commands.start, commands=["start"])
    dp.register_message_handler(users.commands.bot_help, commands=["help"])
    dp.register_message_handler(users.attachments.sticker, content_types=ContentType.STICKER)

    logging.debug("Handlers are registered.")
