from providers.GenericProvider import GenericProvider
import hashlib
import json
import requests


class WordpressProvider(GenericProvider):

    def __init__(self, config: dict, default_config: dict):
        super(WordpressProvider, self).__init__(config, default_config)
        self.call_url = f"{self.config['url']}/wp-json/wp/v2/posts"
        if self.config['search']:
            self.call_url += f"?search={self.config['search_phrase']}"

    def get_new_entries(self):
        req = self.scraper.get(self.call_url, headers={
            'User-Agent': self.config['user_agent']
        })
        if req.status_code == requests.codes.ok:
            req_json = json.loads(req.text)
            entries = {}
            for entry in req_json:
                id_ = hashlib.sha1((self.config['url'] + entry['id']).encode('utf-8')).hexdigest()
                entries[id_] = {
                    'link': entry['link'],
                    'title': entry['title']['rendered']
                }
            new_entries_id = list(set(entries.keys()) - set(self.data.keys()))
            return new_entries_id, entries
        else:
            pass
