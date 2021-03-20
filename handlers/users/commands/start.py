from aiogram import types
from aiogram.dispatcher.webhook import SendMessage


async def start(message: types.Message):
    return SendMessage(message.from_user.id, f"Привет, {message.from_user.full_name}!\n Помощь тут - /help")
