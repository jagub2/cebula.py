from cebula_common import *
from abc import ABC, abstractmethod
from collections import deque
import copy
import cfscrape
import threading


class GenericProvider(ABC):

    def __init__(self, queue: deque, config: dict):
        lock = threading.Lock()
        with lock:
            self.config = copy.deepcopy(config)
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
        for id_ in ids:
            if not any(word.lower() in self.data[id_]['title'].lower() or
                       remove_accents(word.lower()) in self.data[id_]['title'].lower()
                       for word in self.config['exclude']):
                lock = threading.Lock()
                with lock:
                    self.queue.append(self.data[id_])
        config_hash = sha1sum(repr(sorted_dict(self.config)))
        if does_pickle_exist(config_hash):
            write_pickle(config_hash, self)
