from aiogram import types
from aiogram.dispatcher.webhook import SendMessage
from utils.models import Users


async def bot_help(message: types.Message, user: Users):
    return SendMessage(
        message.from_user.id,
        "\n".join(
            [
                f"Hello {user.username}",
                "Пришли мне анимированный стикер, а после ответом на него любой текст",
                "Список команд: ",
                "/start - Начать диалог",
                "/help - Получить справку",
            ]
        ),
    )
