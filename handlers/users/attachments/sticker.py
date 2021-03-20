from aiogram import types


async def sticker(message: types.Message):
    if not message.sticker.is_animated:
        await message.answer("Нужен анимированный стикер =(")
        return
