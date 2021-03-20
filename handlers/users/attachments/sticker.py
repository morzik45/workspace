from aiogram.dispatcher.webhook import SendSticker, DeleteMessage
from aiogram import types
from aiogram.types.force_reply import ForceReply


async def sticker(message: types.Message):
    if not message.sticker.is_animated:
        await message.answer("Нужен анимированный стикер =(")
        return

    # await message.delete()
    return [
        DeleteMessage(chat_id=message.chat.id, message_id=message.message_id),
        SendSticker(
            message.from_user.id,
            sticker=message.sticker.file_id,
            reply_markup=ForceReply(True),
        ),
    ]
