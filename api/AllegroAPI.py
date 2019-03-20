from bs4 import BeautifulSoup
from typing import Pattern
from urllib.parse import urlparse, ParseResult
import json
import re
import requests
import time


class AllegroAPIHandler:
    def __init__(self, client_id, client_secret, sandbox=True):
        self.client_id = client_id
        self.client_secret = client_secret
        self.device_code = None
        self.interval = 0
        self.api_domain = "allegro.pl"
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = 0
        self.orig_html_soup = None
        self.orig_url = None
        if sandbox:
            self.api_domain = "allegro.pl.allegrosandbox.pl"

    def login(self):
        req = requests.post(f"https://{self.api_domain}/auth/oauth/device",
                            auth=(self.client_id, self.client_secret),
                            data={'client_id': self.client_id})
        print(req.status_code)
        if req.status_code == requests.codes.ok:
            response = json.loads(req.text)
            self.device_code = response['device_code']
            self.interval = response['interval']
            return response['verification_uri_complete']

    def authorize_device(self, failures=0):
        req = requests.post(f"https://{self.api_domain}/auth/oauth/token?grant_type="
                            f"urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code&device_code="
                            f"{self.device_code}",
                            auth=(self.client_id, self.client_secret))
        if req.status_code != requests.codes.ok:
            time.sleep(self.interval)
            self.authorize_device(failures=failures + 1)
        else:
            response = json.loads(req.text)
            self.access_token = response['access_token']
            self.refresh_token = response['refresh_token']
            self.token_expiry = response['expires_in']

    def call_api(self, url, post=False, data=None):
        if url.startswith('/'):
            url = url[1:]
        if post:
            req = requests.post(f"https://api.{self.api_domain}/{url}", headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/vnd.allegro.public.v1+json"
            }, data=data)
        else:
            req = requests.get(f"https://api.{self.api_domain}/{url}", headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/vnd.allegro.public.v1+json"
            })
        return req

    def call_orig_url(self, url):
        self.orig_url = url
        req = requests.get(self.orig_url)
        if req.status_code == requests.codes.ok:
            self.orig_html_soup = BeautifulSoup(req.text, features="html.parser")

    def extract_category_id_from_orig_url(self):
        category = None
        if self.orig_html_soup:
            categories_pattern: Pattern[str] = re.compile(r"window.__listing_CategoryTreeState\s*=\s*([^;]*);")
            for script in self.orig_html_soup.find_all('script', {'src': False}):
                if script:
                    match = categories_pattern.search(script.string)
                    if match:
                        categories_json = json.loads(match.group(1))
                        category_from_json: str = categories_json['path'][-1]['id']
                        if category_from_json.isdigit():
                            category = int(category_from_json)
        return category

    def extract_api_filters(self, category_id):
        category_id_str = ""
        if category_id is not None:
            category_id_str = f"category.id={category_id}"
        req = self.call_api(f"/offers/listing?{category_id_str}&fallback=true&include=-all&include=filters")
        if req.status_code == requests.codes.ok:
            json_ = json.loads(req.text)
            return json_['filters']
        return None

    def extract_url_filters(self):
        filters = []
        category_id = self.extract_category_id_from_orig_url()
        api_filters = self.extract_api_filters(category_id)
        parsed_uri: ParseResult = urlparse(self.orig_url)
        for query_param in parsed_uri.query.split('&'):
            param, value = query_param.split('=')
            if param == 'string':
                filters.append(("phrase", value))
        if self.orig_html_soup:
            filters_pattern: Pattern[str] = re.compile(r"window.__listing_FiltersStoreState\s*=\s*([^;]*);")
            for script in self.orig_html_soup.find_all('script', {'src': False}):
                if script:
                    match = filters_pattern.search(script.string)
                    if match:
                        filters_json = json.loads(match.group(1))

                        for slot in filters_json['slots']:
                            for filter_ in slot['filters']:
                                for filter_values in filter_['filterValues']:
                                    if filter_values['selected']:
                                        if filter_['id'].isdigit():
                                            if int(filter_values['raw']['value']) != 1:
                                                filters.append((f"parameter.{filter_['id']}",
                                                                f"{filter_values['raw']['value']}"))
                                            else:
                                                param_value = re.sub(r'([A-Z])', r'_\1', filter_['raw']['id']). \
                                                    upper()
                                                filters.append((f"parameter.{filter_['id']}",
                                                                f"{param_value}"))
                                        else:
                                            if api_filters:
                                                for api_filter in api_filters:
                                                    for api_filter_value in api_filter['values']:
                                                        if api_filter_value['name'] == filter_values['name'] or \
                                                                api_filter_value['name'] == filter_['name']:
                                                            filters.append((api_filter['id'],
                                                                            api_filter_value['value']))

        return filters

    def get_api_domain(self):
        return self.api_domain
