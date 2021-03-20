from aiogram import types
from aiogram.dispatcher.webhook import SendMessage


async def bot_help(message: types.Message):
    return SendMessage(
        message.from_user.id, "\n".join(["Список команд: ", "/start - Начать диалог", "/help - Получить справку"])
    )
