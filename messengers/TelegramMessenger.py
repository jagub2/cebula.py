# pylint: disable=C0111,C0301
from collections import deque
from telegram.error import TelegramError, TimedOut, NetworkError
from telegram.ext import Updater, messagequeue
from messengers import GenericMessenger
import time
import threading
import traceback
import telegram.bot


# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Avoiding-flood-limits
class MQBot(telegram.bot.Bot):

    """A subclass of Bot which delegates send method handling to MQ"""
    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or messagequeue.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except Exception as e:
            pass
        super(MQBot, self).__del__()

    @messagequeue.queuedmessage
    def send_message(self, *args, **kwargs):
        """Wrapped method would accept new `queued` and `isgroup`
        OPTIONAL arguments"""
        return super(MQBot, self).send_message(*args, **kwargs)


class TelegramMessenger(GenericMessenger.GenericMessenger):

    def __init__(self, queue: deque, api_key: str, master: int):
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
                lock = threading.Lock()
                with lock:
                    if len(self.queue) > 0:
                        data = self.queue.pop()
                        self.dispatcher.bot.send_message(chat_id=self.master, text=f"{data['title']}: {data['link']}")
                        if 'photo' in data:
                            self.dispatcher.bot.send_photo(chat_id=self.master, photo=data['photo'])
            except (TimedOut, NetworkError, TelegramError) as e:
                print(f"TelegramBot: Got exception: {e}")
                traceback.print_stack()
                self.connect()
                self.queue_loop()

    def halt(self):
        self.keep_running = False
        self.updater.stop()
