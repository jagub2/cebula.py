from providers.GenericProvider import GenericProvider
from api.AllegroAPI import AllegroAPIHandler, call_orig_url
from urllib.parse import urlencode
from queue import Queue
import json
import hashlib
import requests


class AllegroProvider(GenericProvider):

    def __init__(self, queue: Queue, config: dict):
        super(AllegroProvider, self).__init__(queue, config)
        self.allegro_api = AllegroAPIHandler(self.config['client_id'], self.config['client_secret'],
                                             self.config['use_sandbox'], self.config['max_failures'])
        print(self.allegro_api.login())
        self.allegro_api.authorize_device()
        self.api_soup = call_orig_url(self.config['url'])
        self.filters = self.allegro_api.extract_url_filters(self.config['url'], self.api_soup)
        self.limit = 60
        if 'limit' in self.config:
            self.limit = self.config['limit']

    def get_new_entries(self):
        offers = {'promoted': [], 'regular': []}
        page = 0
        entries = {}
        entries_ids = []
        while len(offers['regular']) < self.limit:
            req = self.allegro_api.call_api(f"/offers/listing?{urlencode(self.filters)}&offset={page * self.limit}")
            if req.status_code == requests.codes.ok:
                offers_new = json.loads(req.text)
                offers['promoted'].extend(offers_new['items']['promoted'])
                offers['regular'].extend(offers_new['items']['regular'])
                accepted_types = ['regular']
                if 'include_promoted' in self.config and self.config['include_promoted']:
                    accepted_types.append('promoted')
                for offer_type in accepted_types:
                    for offer in offers[offer_type]:
                        id_ = hashlib.sha1(f"{self.config['url']}{str(offer['id'])}".encode('utf-8')).hexdigest()
                        entries[id_] = {
                            'link': f"https://{self.allegro_api.get_api_domain()}/oferta/{offer['id']}",
                            'title': offer['name']
                        }
                        entries_ids.append(id_)
            page += 1
        new_entries_id = [entry for entry in list(dict.fromkeys(entries_ids)) if entry not in self.data.keys()]
        return new_entries_id, entries
