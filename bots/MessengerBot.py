from messengers import *
import threading
import messengers


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
        self.bot.connect()
        self.bot.queue_loop()

    def halt(self):
        self.bot.halt()
