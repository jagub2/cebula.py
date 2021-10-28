from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
import hashlib
import json


@for_all_methods(logger.catch)
class ExternalProvider(GenericProvider):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        super().__init__(queue, config, id_list)
        self.redis_key = self.config['redis_key']

    def get_new_entries(self) -> dict:
        entries = {}
        external_entries = self.id_list.redis.lrange(self.redis_key)
        if len(external_entries) > 0:
            for json_entry in external_entries:
                try:
                    entry = json.loads(json_entry)
                    id = hashlib.md5(f"{entry[0]}-{entry[1]}")
                    entries[id] = {
                        'link': entry[1],
                        'title': entry[0]
                    }
                except json.decoder.JSONDecodeError:
                    continue

        return entries
