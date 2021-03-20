import asyncio
import functools
import itertools
import json

from aiogram import types
from aiogram.dispatcher.webhook import BaseResponse
from aiogram.utils.exceptions import TimeoutWarning
from aiogram import Bot, Dispatcher

RESPONSE_TIMEOUT = 55


class WebhookRequestHandler:
    def __init__(self, dp: Dispatcher):
        self.dispatcher = dp
        try:
            Dispatcher.set_current(dp)
            Bot.set_current(dp.bot)
        except RuntimeError:
            pass

    async def parse_update(self, event):
        """
        Read update from stream and deserialize it.

        :param event:
        :return: :class:`aiogram.types.Update`
        """
        data = json.loads(event["body"])
        update = types.Update.to_object(data)
        return update

    async def post(self, event: dict):
        """
        Process POST request

        if one of handler returns instance of :class:`aiogram.dispatcher.webhook.BaseResponse` return it to webhook.
        Otherwise do nothing (return 'ok')

        :return: :dict:
        """

        update = await self.parse_update(event)

        results = await self.process_update(update)
        response = self.get_response(results)

        return {
            "headers": {
                "Content-Type": "application/json",
            },
            "statusCode": 200,
            "body": json.dumps(response.get_response()) if response else "ok",
        }

    async def process_update(self, update):
        """
        Need respond in less than 60 seconds in to webhook.

        So... If you respond greater than 55 seconds webhook automatically respond 'ok'
        and execute callback response via simple HTTP request.

        :param update:
        :return:
        """
        dispatcher = self.dispatcher
        loop = dispatcher.loop or asyncio.get_event_loop()

        # Analog of `asyncio.wait_for` but without cancelling task
        waiter = loop.create_future()
        timeout_handle = loop.call_later(RESPONSE_TIMEOUT, asyncio.tasks._release_waiter, waiter)
        cb = functools.partial(asyncio.tasks._release_waiter, waiter)

        fut = asyncio.ensure_future(dispatcher.updates_handler.notify(update), loop=loop)
        fut.add_done_callback(cb)

        try:
            try:
                await waiter
            except asyncio.CancelledError:
                fut.remove_done_callback(cb)
                fut.cancel()
                raise

            if fut.done():
                return fut.result()
            else:
                # context.set_value(WEBHOOK_CONNECTION, False)
                fut.remove_done_callback(cb)
                fut.add_done_callback(self.respond_via_request)
        finally:
            timeout_handle.cancel()

    def respond_via_request(self, task):
        """
        Handle response after 55 second.

        :param task:
        :return:
        """
        print(
            f"Detected slow response into webhook. "
            f"(Greater than {RESPONSE_TIMEOUT} seconds)\n"
            f"Recommended to use 'async_task' decorator from Dispatcher for handler with long timeouts.",
            TimeoutWarning,
        )

        dispatcher = self.dispatcher
        loop = dispatcher.loop or asyncio.get_event_loop()

        try:
            results = task.result()
        except Exception as e:
            loop.create_task(dispatcher.errors_handlers.notify(dispatcher, types.Update.get_current(), e))
        else:
            response = self.get_response(results)
            if response is not None:
                asyncio.ensure_future(response.execute_response(dispatcher.bot), loop=loop)

    def get_response(self, results):
        """
        Get response object from results.

        :param results: list
        :return:
        """
        if results is None:
            return None
        for result in itertools.chain.from_iterable(results):
            if isinstance(result, BaseResponse):
                return result
