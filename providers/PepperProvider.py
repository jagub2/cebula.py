from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
from bs4 import BeautifulSoup
from collections import deque
import re
import requests


@for_all_methods(logger.catch)
class PepperProvider(GenericProvider):

    def get_new_entries(self) -> dict:
        req = self.scraper.get(self.url, headers={
            'User-Agent': self.config['user_agent'],
            'Accept': '*/*',
            'Referer': self.url
        })
        entries = {}
        if req.status_code == requests.codes.ok: #pylint: disable=no-member
            soup = BeautifulSoup(req.text, features="lxml")
            for offer in soup.find_all('article', {'class': 'thread--deal'}):
                id_ = sha1sum(f"{self.__class__.__name__}{offer['id']}")
                if self.id_list.is_id_present(id_):
                    continue
                if 'min_temp' in self.config:
                    temperature_tag: BeautifulSoup.Tag = offer.find('div', {'class': 'vote-box'})
                    if temperature_tag:
                        temperature = re.sub(r'\D+', '', temperature_tag.text.strip())
                        if int(temperature) < int(self.config['min_temp']):
                            continue
                    else:
                        continue
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

        return entries
