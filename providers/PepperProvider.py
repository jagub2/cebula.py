from providers.GenericProvider import GenericProvider
from bs4 import BeautifulSoup
import hashlib
import requests


class PepperProvider(GenericProvider):

    def __init__(self, config: dict, default_config: dict):
        super(PepperProvider, self).__init__(config, default_config)

    def get_new_entries(self):
        req = requests.get(self.url, headers={
            'User-Agent': self.config['user_agent']
        })
        if req.status_code == requests.codes.ok:
            soup = BeautifulSoup(req.text, features="html.parser")
            entries = {}
            for offer in soup.find_all('article', {'class': 'thread--deal'}):
                id_ = hashlib.sha1((self.config['url'] + offer['id']).encode('utf-8')).hexdigest()
                link = offer.find('a', {'class': 'thread-link'})
                url = link['href'].strip()
                title = link.text.strip()
                entries[id_] = {
                    'link': url,
                    'title': title
                }

            new_entries_id = list(set(entries.keys()) - set(self.data.keys()))
            return new_entries_id, entries
        else:
            pass
