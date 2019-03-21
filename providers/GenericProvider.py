from abc import ABC, abstractmethod
import copy
import cfscrape


class GenericProvider(ABC):

    def __init__(self, config: dict, default_config: dict):
        self.config = copy.deepcopy(default_config)
        self.config.update(config)
        self.data = {}
        self.url = config['url']
        self.call_url = None
        self.scraper = cfscrape.create_scraper()

    @abstractmethod
    def get_new_entries(self):
        pass

    def scan(self):
        ids, self.data = self.get_new_entries()
        self.notify(ids)

    def notify(self, ids):
        for id_ in ids:
            if not any(word.lower() in self.data[id_]['title'].lower() for word in self.config['exclude']):
                print(self.data[id_]['title'])
