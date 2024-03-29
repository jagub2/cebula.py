from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
from collections import deque
import json
import requests


@for_all_methods(logger.catch)
class WordpressProvider(GenericProvider):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        super().__init__(queue, config, id_list)
        self.call_url = f"{self.config['url']}/wp-json/wp/v2/posts"
        if 'search_phrase' in self.config:
            self.call_url += f"?search={self.config['search_phrase']}"

    def get_new_entries(self) -> dict:
        req = self.scraper.get(self.call_url, headers={
            'User-Agent': self.config['user_agent']
        })
        entries = {}
        if req.status_code == requests.codes.ok: #pylint: disable=no-member
            req_json = req.json()
            for entry in req_json:
                id_ = sha1sum(f"{self.__class__.__name__}{entry['id']}")
                if self.id_list.is_id_present(id_):
                    continue
                photo_url = None
                if 'include_photos' in self.config and self.config['include_photos'] and \
                        '_links' in entry and \
                        'wp:featuredmedia' in entry['_links'] and \
                        len(entry['_links']['wp:featuredmedia']) > 0:
                    media_req = self.scraper.get(entry['_links']['wp:featuredmedia'][0]['href'])
                    if media_req.status_code == requests.codes.ok: #pylint: disable=no-member
                        media_json = json.loads(media_req.text)
                        if 'guid' in media_json and 'rendered' in media_json['guid']:
                            photo_url = media_json['guid']['rendered']
                entries[id_] = {
                    'link': entry['link'],
                    'title': entry['title']['rendered']
                }
                if photo_url:
                    entries[id_]['photos'] = [photo_url]

        return entries
