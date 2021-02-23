from cebula_common import * #pylint: disable=unused-wildcard-import
from abc import ABC, abstractmethod
from collections import deque
from loguru import logger
import cfscrape
import threading


@for_all_methods(logger.catch)
class GenericProvider(ABC):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        lock = threading.Lock()
        with lock:
            self.config = config.copy()
        self.id_list = id_list
        self.url = config['url']
        self.call_url = None
        self.scraper = cfscrape.create_scraper()
        self.queue = queue

    @abstractmethod
    def get_new_entries(self) -> dict:
        pass

    def scan(self):
        logger.info(f'{self.__class__.__name__} @ {sha1sum(repr(sorted_dict(self.config)))}: scanning')
        data = self.get_new_entries()
        self.notify(data)
        self.id_list.put_ids(data.keys())

    def notify(self, data: dict):
        i = 0
        for id_, id_data in data.items():
            if not any(word.lower() in id_data['title'].lower() or
                       remove_accents(word.lower()) in id_data['title'].lower()
                       for word in self.config['exclude']) and \
                    not self.id_list.is_id_present(id_):
                lock = threading.Lock()
                with lock:
                    self.queue.append(id_data)
                    i += 1
        logger.info(f'{self.__class__.__name__} @ {sha1sum(repr(sorted_dict(self.config)))}: got {i} entries')
        config_hash = sha1sum(repr(sorted_dict(self.config)))
        if does_pickle_exist(config_hash, self.__class__.__name__):
            write_pickle(config_hash, self)

    def __getstate__(self):
        lock = threading.Lock()
        with lock:
            state_dict = self.__dict__.copy()
            del state_dict['id_list']
            del state_dict['queue']
            return state_dict