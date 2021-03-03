from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
from urllib.parse import urlencode, urlparse
from collections import deque
import json
import random
import requests
import time


# https://github.com/allegro/allegro-api/issues/4213 :)

@for_all_methods(logger.catch)
class AllegroScraperProvider(GenericProvider):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        super().__init__(queue, config, id_list)
        self.limit = 60
        if 'limit' in self.config:
            self.limit = self.config['limit']
        self.parsed_uri = urlparse(self.config['url'])

        self.scraper = cfscrape.create_scraper()

    def get_new_entries(self) -> dict:
        include_promoted = False
        if 'include_promoted' in self.config and self.config['include_promoted']:
            include_promoted = True

        page = 1
        regular_offers = 0
        entries = {}
        still_process_results = True
        while regular_offers < self.limit and still_process_results:
            time.sleep(random.randrange(5, 20))
            call_url = self.url
            if page > 1:
                if not call_url.endswith('&'):
                    call_url += '&'
                call_url += f'p={page}'

            req = self.scraper.get(call_url, headers={
                'User-Agent': self.config['user_agent'],
                'Accept': 'application/json',
                'Accept-Language': 'pl, en-US, en;q=0.5',
                'Referer': self.url,
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache'
            })
            if req.status_code == requests.codes.ok: #pylint: disable=no-member
                json_obj = req.json()
                if not 'items-v3' in json_obj and not 'items' in json_obj['items-v3'] and not 'elements' in json_obj['items-v3']['items']:
                    continue
                elements = json_obj['items-v3']['items']['elements']

                if page >= json_obj['listing']['searchMeta']['lastAvailablePage']:
                    still_process_results = False

                for element in elements:
                    if not all(x in element.keys() for x in ['type', 'id', 'images', 'name', 'promoted']):
                        continue
                    if element['type'] in ['label', 'advertisement', 'advert_external'] or (element['promoted'] and not include_promoted):
                        continue
                    id_ = sha1sum(f"{self.__class__.__name__}{element['id']}")
                    if self.id_list.is_id_present(id_):
                        continue

                    if not element['promoted']:
                        regular_offers += 1
                    link = f"{self.parsed_uri.scheme}://{self.parsed_uri.netloc}/oferta/{element['id']}"
                    title = element['name'].strip()
                    entries[id_] = {
                         'link': link,
                         'title': title
                    }

                    if 'include_photos' in self.config and self.config['include_photos']:
                        entries[id_]['photos'] = [x['url'] for x in element['images']]

            page += 1

        self.reg = regular_offers

        return entries


