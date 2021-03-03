from cebula_common import * #pylint: disable=unused-wildcard-import
from abc import ABC, abstractmethod
from collections import deque
from fake_useragent import UserAgent, FakeUserAgentError
from loguru import logger
import cfscrape


@for_all_methods(logger.catch)
class GenericProvider(ABC):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        self.config = config.copy()
        self.id_list = id_list
        self.url = config['url']
        self.call_url = None
        self.scraper = cfscrape.create_scraper()
        self.queue = queue

        self.user_agent_randomizer = None
        self.set_user_agent_randomizer()

    def set_user_agent_randomizer(self):
        try:
            self.user_agent_randomizer = UserAgent(verify_ssl=False)
        except FakeUserAgentError:
            self.user_agent_randomizer = UserAgent(verify_ssl=False, use_cache_server=False)

    @abstractmethod
    def get_new_entries(self) -> dict:
        pass

    def scan(self):
        logger.debug(f'{self.__class__.__name__} @ {sha1sum(repr(sorted_dict(self.config)))}: scanning')
        if 'randomize_user_agent' in self.config and self.config['randomize_user_agent']:
            self.config['user_agent'] = self.user_agent_randomizer.random
        data = self.get_new_entries()
        if data:
            self.notify(data)
            self.id_list.put_ids(data.keys())
        else:
            logger.debug(f'{self.__class__.__name__} @ {sha1sum(repr(sorted_dict(self.config)))}: no new entries')

    def notify(self, data: dict):
        i = 0
        for id_, id_data in data.items():
            if not any(word.lower() in id_data['title'].lower() or
                       remove_accents(word.lower()) in id_data['title'].lower()
                       for word in self.config['exclude']) and \
                    not self.id_list.is_id_present(id_):
                self.queue.append(id_data)
                i += 1
        if i > 0:
            logger.info(f'{self.__class__.__name__} @ {sha1sum(repr(sorted_dict(self.config)))}: got {i} {"entries" if i != 1 else "entry"}')

    def __getstate__(self):
        state_dict = self.__dict__.copy()
        del state_dict['id_list']
        del state_dict['queue']
        del state_dict['user_agent_randomizer']
        return state_dict

    def __setstate__(self, state_dict):
        state_dict['user_agent_randomizer'] = None
        self.__dict__ = state_dict
        self.set_user_agent_randomizer()
