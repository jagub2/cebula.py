from cebula_common import *
from bs4 import BeautifulSoup
from typing import Pattern
from urllib.parse import urlparse, ParseResult
import datetime
import json
import re
import requests
import threading
import time


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            param_hash = ''
            if 'client_id' in kwargs:
                param_hash += kwargs['client_id']
            else:
                param_hash += args[0]
            if 'client_secret' in kwargs:
                param_hash += kwargs['client_secret']
            else:
                param_hash += args[1]
            pickle_name = sha1sum(param_hash)
            if does_pickle_exist(pickle_name, 'AllegroAPIHandler'):
                cls._instances[cls] = load_pickle(pickle_name, 'AllegroAPIHandler')
            else:
                cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
                write_pickle(pickle_name, cls._instances[cls])
        return cls._instances[cls]


class AllegroAPIHandler(metaclass=Singleton):

    def __init__(self, client_id, client_secret, sandbox=False, max_failures=20):
        self.client_id = client_id
        self.client_secret = client_secret
        self.device_code = None
        self.interval = 0
        self.api_domain = 'allegro.pl'
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.max_failures = max_failures
        self.initialized = False
        self.login_in_progress = False
        if sandbox:
            self.api_domain = 'allegro.pl.allegrosandbox.pl'
        print('Allegro API: __init__')

    def login(self):
        lock = threading.Lock()
        with lock:
            if (self.initialized and self.check_validity_of_login()) or self.login_in_progress:
                return
            print('Allegro API: login loop')
            self.login_in_progress = True
            req = requests.post(f"https://{self.api_domain}/auth/oauth/device",
                                auth=(self.client_id, self.client_secret),
                                data={'client_id': self.client_id})
            if req.status_code == requests.codes.ok:
                print('Allegro API: login ok')
                response = req.json()
                self.device_code = response['device_code']
                self.interval = response['interval']
                return response['verification_uri_complete']

    def authorize_device(self, failures=0):
        lock = threading.Lock()
        with lock:
            if self.initialized and self.check_validity_of_login():
                return
            if failures > self.max_failures:
                return
            req = requests.post(f"https://{self.api_domain}/auth/oauth/token?grant_type="
                                f"urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Adevice_code&device_code="
                                f"{self.device_code}",
                                auth=(self.client_id, self.client_secret))
            if req.status_code != requests.codes.ok:
                time.sleep(self.interval)
                self.authorize_device(failures=failures + 1)
            else:
                current_time = datetime.datetime.now()
                response = req.json()
                self.access_token = response['access_token']
                self.refresh_token = response['refresh_token']
                self.token_expiry = current_time + datetime.timedelta(seconds=int(response['expires_in']))
                self.initialized = True
                self.login_in_progress = False
                print('Allegro API: authorized device')
                self.update_pickle()

    def call_api(self, url, method='GET', **kwargs):
        lock = threading.Lock()
        with lock:
            self.check_tokens_validity_time_and_renew_if_needed()
            if url.startswith('/'):
                url = url[1:]
            req = requests.request(method, f"https://api.{self.api_domain}/{url}", headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/vnd.allegro.public.v1+json"
            }, **kwargs)
            return req

    def check_tokens_validity_time_and_renew_if_needed(self):
        current_time = datetime.datetime.now()
        if timestamps_difference(self.token_expiry, current_time) < self.max_failures:
            print('Allegro API: need renewing tokens')
            self.renew_tokens()

    def renew_tokens(self):
        lock = threading.Lock()
        with lock:
            req = requests.post(f"https://{self.api_domain}/auth/oauth/token?grant_type=refresh_token"
                                f"&refresh_token={self.refresh_token}",
                                auth=(self.client_id, self.client_secret))
            print('Allegro API: posted renew')
            if req.status_code == requests.codes.ok:
                print('Allegro API: renew ok')
                current_time = datetime.datetime.now()
                response = req.json()
                self.access_token = response['access_token']
                self.refresh_token = response['refresh_token']
                self.token_expiry = current_time + datetime.timedelta(seconds=int(response['expires_in']))
                self.update_pickle()

    def extract_api_filters(self, category_id, search_phrase):
        lock = threading.Lock()
        with lock:
            api_call_str = ""
            if category_id is not None:
                api_call_str = f"category.id={category_id}"
            if search_phrase != '':
                api_call_str = f"&phrase={search_phrase}"
            req = self.call_api(f"/offers/listing?{api_call_str}&fallback=true&include=-all&include=filters")
            if req.status_code == requests.codes.ok:
                json_ = req.json()
                return json_['filters']
            return None

    def extract_url_filters(self, url, soup):
        filters = []
        category_id = extract_category_id_from_orig_url(soup, url)
        parsed_uri: ParseResult = urlparse(url)
        search_phrase = ''
        for query_param in parsed_uri.query.split('&'):
            if len(query_param.split('=')) > 1:
                param, value = query_param.split('=')
                if param == 'string':
                    filters.append(('phrase', value))
                    search_phrase = value
                elif param == 'order':
                    sort_map = {
                        'p': '-price',
                        'pd': '+price',
                        'd': '-withDeliveryPrice',
                        'dd': '+withDeliveryPrice',
                        'qd': '-popularity',
                        't': '+endTime',
                        'n': '-startTime',
                    }
                    filters.append(('sort', sort_map[value]))
        if category_id:
            filters.append(('category.id', category_id))
        api_filters = self.extract_api_filters(category_id, search_phrase)
        # \x00-\x1F, \x7F, \x80-\x9F are non-printable unicode characters
        json_regex: Pattern[str] = re.compile(r"[(:]\s*({[^\x00-\x1F\x80-\x9F\x7F;]+})[^;]")
        unquoted_keys: Pattern[str] = re.compile(r"\s*([a-zA-Z]+):")
        dangling_comma: Pattern[str] = re.compile(r",\s*}")
        js_objects: Pattern[str] = re.compile(r":\s*new [^,]+")
        if soup:
            for script in soup.find_all('script', {'src': False}):
                if script and script.contents and len(script.contents) > 0 and 'filterValues' in script.contents[0]:
                    contents = script.contents[0].replace('\n', '')
                    match = json_regex.search(contents)
                    if match:
                        json_data_str = match.group(1)
                        json_data_str = json_data_str.replace('\'', '"')
                        json_data_str = re.sub(unquoted_keys, r'"\1":', json_data_str)
                        json_data_str = re.sub(dangling_comma, "}", json_data_str)
                        json_data_str = re.sub(js_objects, ":null", json_data_str)
                        try:
                            json_data = json.loads(json_data_str)['props']['parameters']['filters']
                        except ValueError as e:
                            continue
                        if 'props' in json_data and 'parameters' in json_data['props'] and \
                                'filters' in json_data['props']['parameters']:
                            for filter_ in json_data['props']['parameters']['filters']:
                                for filter_values in filter_['filterValues']:
                                    if filter_values['selected']:
                                        key_name = None
                                        value_to_normalize_if_needed = filter_values['raw']['id']
                                        value = filter_values['raw']['value']
                                        if filter_['id'].isdigit():
                                            key_name = f"parameter.{filter_['id']}"
                                        else:
                                            if api_filters:
                                                for api_filter in api_filters:
                                                    for api_filter_value in api_filter['values']:
                                                        if api_filter_value['name'] == filter_values['name'] or \
                                                                api_filter_value['name'] == filter_['name']:
                                                            key_name = api_filter['id']
                                                            if 'idSuffix' in api_filter_value:
                                                                key_name += api_filter_value['idSuffix']
                                                            value = api_filter_value['value']

                                        filters.append(
                                            normalized_filter_tuple(
                                                key_name,
                                                value_to_normalize_if_needed,
                                                value
                                            )
                                        )

        return filters

    def get_api_domain(self):
        return self.api_domain

    def check_validity_of_login(self):
        lock = threading.Lock()
        with lock:
            req = self.call_api("/offers/listing?include=-all")
            if req.status_code != requests.codes.ok:
                self.initialized = False
                return False
            return True

    def update_pickle(self):
        lock = threading.Lock()
        with lock:
            print('Allegro API: updating pickle')
            pickle_name = sha1sum(f"{self.client_id}{self.client_secret}")
            if does_pickle_exist(pickle_name, self.__class__.__name__):
                write_pickle(pickle_name, self)


def extract_category_id_from_orig_url(soup, url):
    category = None
    try:
        category = int(url.split('-')[-1].split('?')[0])
    except:
        pass
    finally:
        if category:
            return category
    if soup:
        category_id_pattern: Pattern[str] = re.compile(r"[\"]categoryId[\"]:([^,]+)")
        for script in soup.find_all('script', {'src': False}):
            if script and script.contents and len(script.contents) > 0 and 'categoryId' in script.contents[0]:
                match = category_id_pattern.search(script.contents[0])
                if match:
                    category = match.group(1).strip().replace('"', '')
                    if category.isdigit():
                        category = int(category)
    return category


def call_orig_url(url):
    req = requests.get(url)
    if req.status_code == requests.codes.ok:
        return BeautifulSoup(req.text, features="lxml")


def normalized_filter_tuple(name, value_to_normalize_if_needed, value):
    value_in_tuple = value
    if value.isdigit() and int(value) == 1:
        value_in_tuple = re.sub(r'([A-Z])', r'_\1', value_to_normalize_if_needed).upper()
    return name, value_in_tuple


def timestamps_difference(first_timestamp, second_timestamp):
    delta = first_timestamp - second_timestamp
    return delta.days * 24 * 60 + (delta.seconds + delta.microseconds / 10e6) / 60
