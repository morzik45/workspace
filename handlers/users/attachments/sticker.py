import io

from aiogram import types
from aiogram.dispatcher.webhook import SendSticker
from stickers import TextPrinter


async def sticker(message: types.Message):
    f = io.BytesIO()
    if not message.sticker.is_animated:
        await message.answer("Нужен анимированный стикер =(")
        return
    await message.sticker.download(f)

    tp = TextPrinter(f)
    output = tp.add_text(top_line="Ну начнём", bottom_line="в очередной раз...")

    # await message.bot.send_sticker(
    #     message.from_user.id, types.InputFile(output, filename=".".join([message.sticker.file_unique_id, "tgs"]))
    # )

    return SendSticker(
        message.from_user.id, types.InputFile(output, filename=".".join([message.sticker.file_unique_id, "tgs"]))
    )
