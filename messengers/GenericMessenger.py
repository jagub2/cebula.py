from abc import abstractmethod
from loguru import logger
from cebula_common import for_all_methods


@for_all_methods(logger.catch)
class GenericMessenger:

    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def queue_loop(self):
        pass

    @abstractmethod
    def halt(self):
        pass
