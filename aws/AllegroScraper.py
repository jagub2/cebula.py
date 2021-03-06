import hashlib
import time
from urllib.parse import urlparse, parse_qsl
from loguru import logger
import requests

class AllegroScraper:

    def __init__(self, config):
        needed_keys = ['url', 'user_agent', 'limit']
        self.config = config.copy()
        if not all(x in self.config.keys() for x in needed_keys):
            raise Exception(f"Please provide all config parameters: {', '.join(needed_keys)}")

    @logger.catch
    def get_entries(self):
        result = []

        parsed_uri = urlparse(self.config['url'])
        url_params = dict(parse_qsl(parsed_uri.query))
        url_params['order'] = 'n'

        offset_page = url_params.get('p')
        if offset_page:
            offset_page = int(offset_page)
        else:
            offset_page = 0
        page = 0

        regular_offers = 0
        fetch_results = True

        headers = {
            'User-Agent': self.config['user_agent'],
            'Accept': 'application/json',
            'Accept-Language': 'pl, en-US, en;q=0.5',
            'Referer': self.config['url'],
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }

        while regular_offers < self.config['limit'] and fetch_results:
            page += 1
            time.sleep(1)

            if page > 1:
                url_params['p'] = page + offset_page

            call_url = f"{parsed_uri.scheme}://{parsed_uri.netloc}{parsed_uri.path}"
            logger.debug(f"Got address {call_url}...")

            request = requests.get(call_url, params=url_params, headers=headers)
            logger.debug(f"Trying {request.url}, got {request.status_code}...")

            if request.status_code == requests.codes.ok: #pylint: disable=no-member
                json_obj = request.json()
                if page >= json_obj['listing']['searchMeta']['lastAvailablePage']:
                    fetch_results = False
                elements = [x for x in json_obj['items-v3']['items']['elements'] \
                        if not x['type'] in ['label', 'advertisement', 'advert_external']]
                regular_offers += len([x for x in elements if not x.get('promoted')])
                result += elements
            else:
                # something's wrong, I can feel it
                fetch_results = False
                logger.error(f"Broken reply: {request.text}")

        return result
