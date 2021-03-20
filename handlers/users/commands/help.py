from aiogram import types
from aiogram.dispatcher.webhook import SendMessage


async def bot_help(message: types.Message):
    return SendMessage(
        message.from_user.id,
        "\n".join(
            [
                "Пришли мне анимированный стикер, а после ответом на него любой текст",
                "Список команд: ",
                "/start - Начать диалог",
                "/help - Получить справку",
            ]
        ),
    )
