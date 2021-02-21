from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
from collections import deque
import json
import requests


class WordpressProvider(GenericProvider):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        super(WordpressProvider, self).__init__(queue, config, id_list)
        self.call_url = f"{self.config['url']}/wp-json/wp/v2/posts"
        if 'search_phrase' in self.config:
            self.call_url += f"?search={self.config['search_phrase']}"

    def get_new_entries(self):
        req = self.scraper.get(self.call_url, headers={
            'User-Agent': self.config['user_agent']
        })
        if req.status_code == requests.codes.ok: #pylint: disable=no-member
            req_json = req.json()
            entries = {}
            entries_ids = []
            for entry in req_json:
                id_ = sha1sum(f"{self.__class__.__name__}{entry['id']}")
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
                entries_ids.append(id_)
                if photo_url:
                    entries[id_]['photos'] = [photo_url]
            new_entries_id = [entry for entry in entries_ids if not self.id_list.is_id_present(entry)]
            return new_entries_id, entries
