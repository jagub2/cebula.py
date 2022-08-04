from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
from collections import deque
import requests


@for_all_methods(logger.catch)
class OLXAPIProvider(GenericProvider):

    def get_new_entries(self) -> dict:
        req = self.scraper.get(self.config['url'], headers={'User-Agent': self.config['user_agent']})
        entries = {}
        if req.status_code == requests.codes.ok: #pylint: disable=no-member
            json_data = req.json()
            if not 'data' in json_data:
                return
            for entry in json_data['data']:
                id_ = sha1sum(f"{self.__class__.__name__}{entry['url']}")
                if self.id_list.is_id_present(id_):
                    continue
                entries[id_] = {
                    'link': entry['url'],
                    'title': entry['title']
                }

        return entries
