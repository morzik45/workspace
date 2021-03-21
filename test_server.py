import logging
import os

from aiogram import Bot, filters
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook
from aiogram.types import ContentType

from handlers import users
from middlewares import UserMiddleware

try:
    from dotenv import load_dotenv

    load_dotenv()
except:  # noqa
    pass

API_TOKEN = os.environ.get("TG_TOKEN_TEST")

# webhook settings
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST_TEST")
WEBHOOK_PATH = "/bot/"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = "0.0.0.0"  # or ip
WEBAPP_PORT = 3001

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())
dp.middleware.setup(UserMiddleware())


async def on_startup(dp):
    dp.register_message_handler(users.commands.start, commands=["start"])
    dp.register_message_handler(users.commands.bot_help, commands=["help"])
    dp.register_message_handler(users.attachments.sticker, content_types=ContentType.STICKER)
    dp.register_message_handler(users.messages.say, filters.IsReplyFilter)

    await bot.set_webhook(WEBHOOK_URL)
    # insert code here to run it after start


async def on_shutdown(dp):
    logging.warning("Shutting down..")

    # insert code here to run it before shutdown

    # Remove webhook (not acceptable in some cases)
    await bot.delete_webhook()

    # Close DB connection (if used)
    await dp.storage.close()
    await dp.storage.wait_closed()

    logging.warning("Bye!")


if __name__ == "__main__":

    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        path="bot",
    )
