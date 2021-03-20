import io
import textwrap
from aiogram import types
from aiogram.dispatcher.handler import SkipHandler
from stickers import TextPrinter


async def say(message: types.Message):
    if (
        message.reply_to_message is None
        or not message.reply_to_message.sticker
        or not message.reply_to_message.sticker.is_animated
    ):
        raise SkipHandler

    f = io.BytesIO()

    await message.reply_to_message.sticker.download(f)
    tp = TextPrinter(f)

    list_texts = textwrap.fill(message.text, 16).split("\n")

    output = tp.add_text(top_line=list_texts[0], bottom_line=list_texts[1] if len(list_texts) > 1 else None)

    await message.bot.send_sticker(
        message.from_user.id,
        types.InputFile(output, filename=".".join([message.reply_to_message.sticker.file_unique_id, "tgs"])),
    )
