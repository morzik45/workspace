import logging
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from utils.models import Users

logging


class UserMiddleware(BaseMiddleware):
    def __init__(self):
        super(UserMiddleware, self).__init__()

    async def on_pre_process_message(self, message: types.Message, data: dict):
        if message and message.from_user:
            current_user = Users(
                user_id=message.from_user.id,
                username=message.from_user.username,
                lang="ru" if message.from_user.locale.language.lower() == "ru" else "en",
                refferal=message.get_args(),
            )
            data["user"] = current_user
            logging.warning(current_user.username)
