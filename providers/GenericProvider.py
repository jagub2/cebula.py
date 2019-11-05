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
        self.ids = []
        self.url = config['url']
        self.call_url = None
        self.scraper = cfscrape.create_scraper()
        self.queue = queue

    @abstractmethod
    def get_new_entries(self):
        pass

    def scan(self):
        print(f'{self.__class__.__name__} @ {sha1sum(repr(sorted_dict(self.config)))}: scanning')
        ids, data = self.get_new_entries()
        self.notify(ids, data)
        self.ids.extend(ids)
        if len(self.ids) > self.config['limit'] * self.config['max_failures']:
            self.ids = self.ids[-self.config['limit']:]

    def notify(self, ids, data):
        i = 0
        for id_ in ids:
            if not any(word.lower() in data[id_]['title'].lower() or
                       remove_accents(word.lower()) in data[id_]['title'].lower()
                       for word in self.config['exclude']) and \
                    id_ not in self.ids:
                lock = threading.Lock()
                with lock:
                    self.queue.append(data[id_])
                    i += 1
        print(f'{self.__class__.__name__} @ {sha1sum(repr(sorted_dict(self.config)))}: got {i} entries')
        config_hash = sha1sum(repr(sorted_dict(self.config)))
        if does_pickle_exist(config_hash, self.__class__.__name__):
            write_pickle(config_hash, self)
