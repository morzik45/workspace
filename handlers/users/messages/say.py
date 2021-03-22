import io
import textwrap
from utils.models.users import Users
from aiogram import types
from aiogram.dispatcher.handler import SkipHandler
from stickers import TextPrinter


async def say(message: types.Message, user: Users):
    if (
        message.reply_to_message is None
        or not message.reply_to_message.sticker
        or not message.reply_to_message.sticker.is_animated
    ):
        raise SkipHandler

    f = io.BytesIO()

    await message.reply_to_message.sticker.download(f)
    tp = TextPrinter(f)

    list_texts = textwrap.fill(message.text, 15).split("\n")

    if len(list_texts) == 1:
        output = tp.add_text(top_line=list_texts[0])
    if len(list_texts) == 2:
        output = tp.add_text(top_line=list_texts[0], bottom_line=list_texts[1])
    if len(list_texts) >= 3:
        output = tp.add_text(top_line=list_texts[0], middle_line=list_texts[1], bottom_line=list_texts[2])

    await message.bot.send_sticker(
        message.from_user.id,
        types.InputFile(output, filename=".".join([message.reply_to_message.sticker.file_unique_id, "tgs"])),
    )

    user.stickers_count_incr()
