from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
import hashlib
import json


@for_all_methods(logger.catch)
class ExternalProvider(GenericProvider):

    def get_new_entries(self) -> dict:
        entries = {}
        external_entries = self.id_list.redis.lrange(self.config['redis_key'], 0, -1)
        if len(external_entries) > 0:
            for json_entry in external_entries:
                try:
                    entry = json.loads(json_entry)
                    id_ = hashlib.md5(f"{entry[0]}-{entry[1]}".encode('utf-8')).hexdigest()
                    entries[id_] = {
                        'link': entry[1],
                        'title': entry[0]
                    }
                except json.decoder.JSONDecodeError:
                    continue
        self.id_list.redis.ltrim(self.config['redis_key'], len(external_entries), -1)

        return entries
