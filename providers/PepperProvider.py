from providers.GenericProvider import *
from bs4 import BeautifulSoup
from queue import Queue
import re
import requests


class PepperProvider(GenericProvider):

    def __init__(self, queue: Queue, config: dict):
        super(PepperProvider, self).__init__(queue, config)

    def get_new_entries(self):
        req = self.scraper.get(self.url, headers={
            'User-Agent': self.config['user_agent'],
            'Accept': '*/*',
            'Referer': self.url
        })
        if req.status_code == requests.codes.ok:
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
                id_ = sha1sum(f"{self.config['url']}{offer['id']}")
                link = offer.find('a', {'class': 'thread-link'})
                url = link['href'].strip()
                title = link.text.strip()
                photo_url = None
                if 'include_photos' in self.config and self.config['include_photos']:
                    image = offer.find('img', {'class': 'thread-image'})
                    if image:
                        photo_url = image['src']
                entries[id_] = {
                    'link': url,
                    'title': title
                }
                if photo_url:
                    entries[id_]['photo'] = photo_url
                entries_ids.append(id_)

            new_entries_id = [entry for entry in entries_ids if entry not in self.data.keys()]
            return new_entries_id, entries
        else:
            pass
