# pylint: disable=C0111,C0301
from collections import deque
from loguru import logger
from telegram import InputMediaPhoto
from telegram.message import Message
from telegram.error import *
from telegram.ext import Updater, messagequeue
from cebula_common import for_all_methods
from messengers import GenericMessenger
from pynchronized.pynchronized import thread_synchronized
import time
import threading
import traceback
import telegram.bot


# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Avoiding-flood-limits
@for_all_methods(logger.catch)
@thread_synchronized
class MQBot(telegram.bot.Bot):

    """A subclass of Bot which delegates send method handling to MQ"""
    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super().__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or messagequeue.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except:
            pass

    @messagequeue.queuedmessage
    def send_message(self, *args, **kwargs):
        """Wrapped method would accept new `queued` and `isgroup`
        OPTIONAL arguments"""
        return super(MQBot, self).send_message(*args, **kwargs)


@for_all_methods(logger.catch)
@thread_synchronized
class TelegramMessenger(GenericMessenger.GenericMessenger):

    def __init__(self, queue: deque, api_key: str, master: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.updater, self.dispatcher, self.message_queue, self.bot = None, None, None, None
        self.queue = queue
        self.api_key = api_key
        self.master = master
        self.keep_running = True

    def connect(self):
        self.message_queue = messagequeue.MessageQueue(all_burst_limit=3, all_time_limit_ms=3000)
        self.bot = MQBot(token=self.api_key, mqueue=self.message_queue)
        self.updater = Updater(bot=self.bot)
        self.dispatcher = self.updater.dispatcher
        self.updater.start_polling()
        self.dispatcher.bot.send_message(chat_id=self.master, text="cebula.py started!")

    def queue_loop(self):
        while self.keep_running:
            time.sleep(0.1)
            try:
                if len(self.queue) > 0:
                    returned_data = None
                    data = self.queue.pop()
                    if 'photos' in data and data['photos'] and len(data['photos']) > 0:
                        for i in range(0, len(data['photos']), 10):
                            media = []
                            for photo in data['photos'][i:i + 10]:
                                media.append(InputMediaPhoto(media=photo))
                            media[0].caption = f"{data['title']}: {data['link']}"
                            returned_data = self.dispatcher.bot.send_media_group(chat_id=self.master, media=media)
                    else:
                        returned_data = self.dispatcher.bot.send_message(chat_id=self.master, text=f"{data['title']}: {data['link']}")
                    # check return value, whether it was successful
                    if isinstance(returned_data, Message):
                        returned_data = [returned_data]
                    elif returned_data and not isinstance(returned_data, list):
                        # probably a Promise object, check for its result
                        returned_data = returned_data.result()
                    # retry sending data if unsuccessful
                    if not returned_data or (isinstance(returned_data, list) and len(returned_data) < 1):
                        data_copy = data.copy()
                        if 'photos' in data_copy:
                            del data_copy['photos']
                        self.queue.append(data_copy)
            except (TimedOut, NetworkError, TelegramError, Unauthorized, BadRequest, \
                ChatMigrated, RetryAfter, Conflict, InvalidToken) as e:
                logger.error(f"TelegramBot: Got exception: {e}")
                traceback.print_stack()
                self.connect()
                self.queue_loop()

    def halt(self):
        self.keep_running = False
        self.updater.stop()
