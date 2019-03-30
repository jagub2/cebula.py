# pylint: disable=C0111,C0301
from providers import *
from cebula_common import *
from collections import deque
import time
import threading
import providers


class ProviderBot:

    def __init__(self, queue: deque, bot_class_str: str, config: dict):
        self.keep_running = True
        self.bot: GenericProvider = None
        bot_module = getattr(providers, bot_class_str)
        if bot_module:
            bot_class = getattr(bot_module, bot_class_str)
            if bot_class:
                config_hash = sha1sum(repr(sorted_dict(config)))
                if does_pickle_exist(config_hash):
                    self.bot = load_pickle(config_hash)
                    # we need update reference to queue (deque)
                    self.bot.queue = queue
                else:
                    self.bot = bot_class(queue, config)
                    write_pickle(config_hash, self.bot)
            else:
                self.keep_running = False
        else:
            self.keep_running = False

    def queue_loop(self):
        while self.keep_running:
            try:
                self.bot.scan()
                time.sleep(600)
            except Exception as e:
                print(f"ProviderBot: Got exception: {e}")
                self.queue_loop()

    def halt(self):
        self.keep_running = False


class ProviderThread(threading.Thread):

    def __init__(self, bot_instance: ProviderBot):
        self.bot_instance = bot_instance
        threading.Thread.__init__(self)

    def run(self):
        self.bot_instance.queue_loop()

    def halt(self):
        self.bot_instance.halt()
