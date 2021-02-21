from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
from bs4 import BeautifulSoup
from collections import deque
import re
import requests


@for_all_methods(logger.catch)
class PepperProvider(GenericProvider):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        super(PepperProvider, self).__init__(queue, config, id_list)

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
            for offer in soup.find_all('article', {'class': 'thread--deal'}):
                if 'min_temp' in self.config:
                    temperature_tag: BeautifulSoup.Tag = offer.find('div', {'class': 'vote-box'})
                    if temperature_tag:
                        temperature = re.sub(r'\D+', '', temperature_tag.text.strip())
                        if int(temperature) < int(self.config['min_temp']):
                            continue
                    else:
                        continue
                id_ = sha1sum(f"{self.__class__.__name__}{offer['id']}")
                link = offer.find('a', {'class': 'thread-link'})
                if not link:
                    continue
                url = link['href'].strip()
                title = link.text.strip()
                photo_url = None
                if 'include_photos' in self.config and self.config['include_photos']:
                    image = offer.find('img', {'class': 'thread-image'})
                    if image:
                        photo_url = image.get('src')
                entries[id_] = {
                    'link': url,
                    'title': title
                }
                if photo_url:
                    entries[id_]['photos'] = [photo_url]
                entries_ids.append(id_)

            new_entries_id = [entry for entry in entries_ids if not self.id_list.is_id_present(entry)]
            return new_entries_id, entries
