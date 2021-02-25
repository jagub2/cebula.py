from loguru import logger
from cebula_common import for_all_methods
from messengers import *
import time
import messengers


@for_all_methods(logger.catch)
class MessengerThread(threading.Thread):

    def __init__(self, bot_class_str: str, *args, **kwargs):
        self.bot: GenericMessenger = None
        bot_module = getattr(messengers, bot_class_str)
        if bot_module:
            bot_class = getattr(bot_module, bot_class_str)
            if bot_class:
                self.bot = bot_class(*args, **kwargs)
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.bot.connect()
            self.bot.queue_loop()
        except Exception as e:
            logger.error(f"MessengerThread: Got exception: {e}")
            traceback.print_stack()
            time.sleep(10)
            self.run()

    def halt(self):
        self.bot.halt()
