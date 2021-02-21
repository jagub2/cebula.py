from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlparse
import re
import requests


@for_all_methods(logger.catch)
class EbayKleinanzeigenProvider(GenericProvider):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        super(EbayKleinanzeigenProvider, self).__init__(queue, config, id_list)
        self.parsed_uri = urlparse(self.url)

    def get_new_entries(self):
        req = self.scraper.get(self.url, headers={
            'User-Agent': self.config['user_agent'],
            'Accept': '*/*',
            'Referer': self.url
        })
        if req.status_code == requests.codes.ok: #pylint: disable=no-member
            soup = BeautifulSoup(req.text, features="lxml")
            entries = {}
            entries_ids = []
            for offer in soup.find_all('article', {'class': 'aditem'}):
                id_ = sha1sum(f"{self.__class__.__name__}{offer['data-adid']}")
                link = offer.find('a', {'class': 'ellipsis'})
                url = link['href'].strip()
                if url.startswith('/'):
                    url = f"{self.parsed_uri.scheme}://{self.parsed_uri.netloc}{url}"
                title = link.text.strip()
                photo_url = None
                if 'include_photos' in self.config and self.config['include_photos']:
                    image = offer.find('div', {'class': 'imagebox'})['data-imgsrc']
                entries[id_] = {
                    'link': url,
                    'title': title
                }
                if image:
                    entries[id_]['photos'] = [image]
                entries_ids.append(id_)

            new_entries_id = [entry for entry in entries_ids if not self.id_list.is_id_present(entry)]
            return new_entries_id, entries
        else:
            pass
