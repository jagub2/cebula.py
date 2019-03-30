import copy
import cfscrape
import threading
from abc import ABC, abstractmethod
from queue import Queue


class GenericProvider(ABC):

    def __init__(self, queue: Queue, config: dict, default_config: dict):
        lock = threading.Lock()
        with lock:
            self.config = copy.deepcopy(default_config)
        self.config.update(config)
        self.data = {}
        self.url = config['url']
        self.call_url = None
        self.scraper = cfscrape.create_scraper()
        self.queue = queue

    @abstractmethod
    def get_new_entries(self):
        pass

    def scan(self):
        ids, self.data = self.get_new_entries()
        self.notify(ids)

    def notify(self, ids):
        for id_ in reversed(ids):
            if not any(word.lower() in self.data[id_]['title'].lower() for word in self.config['exclude']):
                self.queue.put(self.data[id_])
