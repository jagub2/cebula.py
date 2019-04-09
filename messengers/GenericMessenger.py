from abc import abstractmethod


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
