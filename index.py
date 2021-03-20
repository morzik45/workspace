import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from webhook import WebhookRequestHandler
from handlers import register_handlers


logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.environ.get("TG_TOKEN", 0), parse_mode="HTML", validate_token=False)
dp = Dispatcher(bot=bot)
dp.middleware.setup(LoggingMiddleware())


async def handler(event, context):
    """Yandex.Cloud functions handler."""
    if event.get("httpMethod") == "POST":
        token = event.get("params", {}).get("token")
        try:
            with dp.bot.with_token(token, validate_token=True):
                await register_handlers(dp=dp)
                return await WebhookRequestHandler(dp=dp).post(event)
        except Exception as e:
            logging.error(e)
        return {"statusCode": 200, "body": "ok"}
    return {"statusCode": 405}
