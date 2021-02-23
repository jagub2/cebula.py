from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
from api.AllegroAPI import AllegroAPIHandler, call_orig_url
from urllib.parse import urlencode
from collections import deque
import json
import requests


@for_all_methods(logger.catch)
class AllegroProvider(GenericProvider):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        super(AllegroProvider, self).__init__(queue, config, id_list)
        self.allegro_api = AllegroAPIHandler(self.config['allegro_client_id'], self.config['allegro_client_secret'],
                                             self.config['use_sandbox'], self.config['max_failures'])
        lock = threading.Lock()
        with lock:
            login_url = self.allegro_api.login()
            if login_url:

                self.queue.append({
                    'title': 'Allegro login',
                    'link': login_url
                })
                self.allegro_api.authorize_device()
        api_soup = call_orig_url(self.config['url'])
        self.filters = self.allegro_api.extract_url_filters(self.config['url'], api_soup)
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
            offers_new = json.loads(req.text)
            if req.status_code == requests.codes.ok: #pylint: disable=no-member
                offers['promoted'].extend(offers_new['items']['promoted'])
                offers['regular'].extend(offers_new['items']['regular'])
                if page * self.limit > offers_new['searchMeta']['availableCount']:
                    break
            else:
                if not self.allegro_api.check_validity_of_login():
                    login_url = self.allegro_api.login()
                    if login_url:
                        lock = threading.Lock()
                        with lock:
                            self.queue.append({
                                'title': 'Allegro login',
                                'link': login_url
                            })
                    break
            page += 1
        accepted_types = ['regular']
        if 'include_promoted' in self.config and self.config['include_promoted']:
            accepted_types.append('promoted')
        for offer_type in accepted_types:
            for offer in offers[offer_type][:self.limit]:
                id_ = str(offer['id'])
                if self.id_list.is_id_present(id_):
                    continue
                offer_link = f"https://{self.allegro_api.get_api_domain()}/oferta/{offer['id']}"
                if 'vendor' in offer and 'url' in offer['vendor']:
                    offer_link = offer['vendor']['url']
                entries[id_] = {
                    'link': offer_link,
                    'title': offer['name']
                }
                if 'include_photos' in self.config and self.config['include_photos']:
                    if 'images' in offer:
                        entries[id_]['photos'] = [x['url'] for x in offer['images']]

                entries_ids.append(id_)
        return entries_ids, entries

    def __getstate__(self):
        lock = threading.Lock()
        with lock:
            state_dict = self.__dict__.copy()
            del state_dict['allegro_api']
            return state_dict

    def __setstate__(self, state_dict):
        state_dict['allegro_api'] = AllegroAPIHandler(state_dict['config']['allegro_client_id'],
                                                      state_dict['config']['allegro_client_secret'],
                                                      state_dict['config']['use_sandbox'],
                                                      state_dict['config']['max_failures'])
        self.__dict__ = state_dict
