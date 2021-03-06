from providers.AWSProvider import AWSProvider
from cebula_common import for_all_methods, sha1sum, IdList
from urllib.parse import urlencode, urlparse
from loguru import logger
from collections import deque
import json
import random
import requests
import time


# https://github.com/allegro/allegro-api/issues/4213 :)

@for_all_methods(logger.catch)
class AllegroAWSScraperProvider(AWSProvider):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        super().__init__(queue, config, id_list)
        self.limit = 60
        if 'limit' in self.config:
            self.limit = self.config['limit']
        self.parsed_uri = urlparse(self.config['url'])

    def get_new_entries(self) -> dict:
        include_promoted = False
        if 'include_promoted' in self.config and self.config['include_promoted']:
            include_promoted = True

        api_url: str = self.config['aws_url']
        if not api_url.endswith('?'):
            api_url += '?'
        api_url += urlencode({'url': self.config['url']})
        req = self.call_api(api_url)

        entries = {}

        if req.status_code == requests.codes.ok: #pylint: disable=no-member
            elements = req.json()

            for element in elements:
                if not all(x in element.keys() for x in ['type', 'id', 'images', 'name', 'promoted', 'url', 'vendor']):
                    continue
                if element['type'] in ['label', 'advertisement', 'advert_external'] or (element['promoted'] and not include_promoted):
                    continue
                id_ = sha1sum(f"{self.__class__.__name__}{element['id']}")
                if self.id_list.is_id_present(id_):
                    continue

                link = f"{self.parsed_uri.scheme}://{self.parsed_uri.netloc}/oferta/{element['id']}"
                if element['vendor'] != 'allegro':
                    link = element['url']
                title = element['name'].strip()
                entries[id_] = {
                        'link': link,
                        'title': title
                }

                if 'include_photos' in self.config and self.config['include_photos']:
                    entries[id_]['photos'] = [x['url'] for x in element['images']]

        return entries
