from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
from bs4 import BeautifulSoup
from collections import deque
from typing import Pattern
from urllib.parse import urlparse
import json
import re
import requests


@for_all_methods(logger.catch)
class OLXProvider(GenericProvider):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        super().__init__(queue, config, id_list)
        parsed_uri = urlparse(self.config['url'])
        self.call_url = f"{parsed_uri.scheme}://{parsed_uri.netloc}/ajax/search/list/"
        self.search_params = []
        self.build_search_args()

    def build_search_args(self):
        def get_hidden_search_fields(tag):
            return tag.has_attr('name') and \
                   tag.has_attr('value') and \
                   tag.name == 'input' and \
                   tag['name'].startswith('search[') and \
                   tag['name'].endswith(']') and \
                   tag['type'] != 'checkbox'  # somehow checkboxes are checked when search params don't mention it

        req = self.scraper.get(self.config['url'], headers={'User-Agent': self.config['user_agent']})
        if req.status_code == requests.codes.ok: #pylint: disable=no-member
            soup = BeautifulSoup(req.text, features="html.parser")
            params_pattern: Pattern[str] = re.compile(r"var\s+geoData\s*=\s*(.*);")
            for input_ in soup.find_all(get_hidden_search_fields):
                self.search_params.append((input_['name'], input_['value']))
            for script in soup.find_all('script', {'src': False}):
                if script:
                    match = params_pattern.search(script.string)
                    if match:
                        params = json.loads(match.group(1))
                        if 'q' in params['params']:
                            self.search_params.append(('q', params['params']['q']))
                        if 'search' in params['params']:
                            for key, value in params['params']['search'].items():
                                if isinstance(value, list):
                                    for arr_value in value:
                                        self.search_params.append((f"search[{key}][]", arr_value))
                                else:
                                    self.search_params.append((f"search[{key}]", value))

    def get_new_entries(self) -> dict:
        req = self.scraper.post(self.call_url, data=self.search_params, headers={
            'User-Agent': self.config['user_agent'],
            'Accept': '*/*',
            'Referer': self.config['url'],
            'X-Requested-With': 'XMLHttpRequest'
        })
        entries = {}
        if req.status_code == requests.codes.ok: #pylint: disable=no-member
            soup = BeautifulSoup(req.text, features="html.parser")
            for offer in soup.find_all('td', {'class': 'offer'}):
                if 'include_promoted' in self.config and not self.config['include_promoted']:
                    if offer.find('span', {'class': 'paid'}) and 'promoted' in offer['class']:
                        continue
                if offer.find('table') and offer.find('a', {'class': 'link'}):
                    id_ = sha1sum(f"{self.__class__.__name__}{offer.find('table')['data-id']}")
                    if self.id_list.is_id_present(id_):
                        continue
                    link = offer.find('a', {'class': 'link'})
                    url = link['href'].strip()
                    title = link.text.strip()
                    entries[id_] = {
                        'link': url,
                        'title': title
                    }
                    if 'include_photos' in self.config and self.config['include_photos']:
                        entries[id_]['photos'] = self.get_photos(url)

        return entries

    def get_photos(self, url: str) -> list:
        req = self.scraper.get(url, headers={
            'User-Agent': self.config['user_agent'],
            'Accept': '*/*',
            'Referer': self.config['url'],
        })
        all_photos = []
        if req.status_code == requests.codes.ok: #pylint: disable=no-member
            soup = BeautifulSoup(req.text, features="html.parser")
            wrapper = soup.find('ul', {'id': 'descGallery'})
            if not wrapper:
                wrapper = soup.find('div', {'id': 'descImage'})
            if wrapper:
                photos = wrapper.find_all('img')
                if not photos:
                    photos = wrapper.find_all('a')
                for photo in photos:
                    src = 'src'
                    if 'href' in photo.attrs:
                        src = 'href'
                    all_photos.append(photo.get(src))
        return all_photos
