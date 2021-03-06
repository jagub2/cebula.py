import requests
from providers.GenericProvider import GenericProvider


class AWSProvider(GenericProvider):

    def call_api(self, url, method='GET', **kwargs):
        req = requests.request(method, url, headers={
            "X-API-Key": self.config['aws_api_key']
        }, **kwargs)
        return req
