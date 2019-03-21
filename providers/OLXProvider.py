from providers.GenericProvider import GenericProvider
from bs4 import BeautifulSoup
from typing import Pattern
from urllib.parse import urlparse
import hashlib
import json
import re
import requests


class OLXProvider(GenericProvider):

    def __init__(self, config: dict, default_config: dict):
        super(OLXProvider, self).__init__(config, default_config)
        parsed_uri = urlparse(self.config['url'])
        self.call_url = f"{parsed_uri.scheme}://{parsed_uri.netloc}/ajax/search/list/"
        self.search_params = []
        self.build_search_args()

    def build_search_args(self):
        def get_hidden_search_fields(tag):
            if tag.has_attr('name') and tag.has_attr('value'):
                return tag.name == 'input' and \
                       tag['name'].startswith('search[') and \
                       tag['name'].endswith(']') and \
                       tag['type'] != 'checkbox'  # somehow checkboxes are checked when search params don't mention it

        req = self.scraper.get(self.config['url'], headers={'User-Agent': self.config['user_agent']})
        if req.status_code == requests.codes.ok:
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
                                if type(value) == list:
                                    for arr_value in value:
                                        self.search_params.append((f"search[{key}][]", arr_value))
                                else:
                                    self.search_params.append((f"search[{key}]", value))

    def get_new_entries(self):
        req = self.scraper.post(self.call_url, data=self.search_params, headers={
            'User-Agent': self.config['user_agent'],
            'Accept': '*/*',
            'Referer': self.config['url'],
            'X-Requested-With': 'XMLHttpRequest'
        })
        if req.status_code == requests.codes.ok:
            soup = BeautifulSoup(req.text, features="html.parser")
            entries = {}
            for offer in soup.find_all('td', {'class': 'offer'}):
                if offer.find('table') and offer.find('a', {'class': 'link'}):
                    id_ = hashlib.sha1((self.config['url'] + offer.find('table')['data-id']).encode('utf-8')).\
                        hexdigest()
                    link = offer.find('a', {'class': 'link'})
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