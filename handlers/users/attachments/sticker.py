from aiogram.dispatcher.webhook import SendMessage
from aiogram import types


async def sticker(message: types.Message):
    if not message.sticker.is_animated:
        await message.answer("Нужен анимированный стикер =(")
        return

    return SendMessage(message.from_user.id, "А теперь любой текст ответом на него")
