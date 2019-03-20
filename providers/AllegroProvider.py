from providers.GenericProvider import GenericProvider
from api.AllegroAPI import AllegroAPIHandler
from urllib.parse import urlencode
import json
import hashlib
import requests


class AllegroProvider(GenericProvider):

    def __init__(self, config: dict, default_config: dict):
        super(AllegroProvider, self).__init__(config, default_config)
        self.allegro_api = AllegroAPIHandler(self.config['client_id'], self.config['client_secret'])
        print(self.allegro_api.login())
        self.allegro_api.authorize_device()
        self.allegro_api.call_orig_url(self.config['url'])
        self.filters = self.allegro_api.extract_url_filters()

    def get_new_entries(self):
        req = self.allegro_api.call_api(f"/offers/listing?{urlencode(self.filters)}")
        if req.status_code == requests.codes.ok:
            offers = json.loads(req.text)
            entries = {}
            for offer_type in ['promoted', 'regular']:
                for offer in offers['items'][offer_type]:
                    id_ = hashlib.sha1(f"{self.config['url']}{str(offer['id'])}".encode('utf-8')).hexdigest()
                    entries[id_] = {
                        'link': f"https://{self.allegro_api.get_api_domain()}/oferta/{offer['id']}",
                        'title': offer['name']
                    }

            new_entries_id = list(set(entries.keys()) - set(self.data.keys()))
            return new_entries_id, entries
        else:
            pass
