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
        super().__init__(queue, config, id_list)
        self.parsed_uri = urlparse(self.url)

    def get_new_entries(self) -> dict:
        req = self.scraper.get(self.url, headers={
            'User-Agent': self.config['user_agent'],
            'Accept': '*/*',
            'Referer': self.url
        })
        entries = {}
        if req.status_code == requests.codes.ok: #pylint: disable=no-member
            soup = BeautifulSoup(req.text, features="lxml")
            for offer in soup.find_all('article', {'class': 'aditem'}):
                id_ = sha1sum(f"{self.__class__.__name__}{offer['data-adid']}")
                if self.id_list.is_id_present(id_):
                    continue
                link = offer.find('a', {'class': 'ellipsis'})
                url = link['href'].strip()
                if url.startswith('/'):
                    url = f"{self.parsed_uri.scheme}://{self.parsed_uri.netloc}{url}"
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
            offer = soup.find('article', {'id': 'viewad-product'})
            if offer:
                photos = offer.find_all('img', {'id': 'viewad-image'})
                for photo in photos:
                    src = 'src'
                    if 'data-imgsrc' in photo.attrs:
                        src = 'data-imgsrc'
                    all_photos.append(photo.get(src))
        return all_photos
