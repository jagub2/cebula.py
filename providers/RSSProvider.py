from providers.GenericProvider import * #pylint: disable=unused-wildcard-import
from cebula_common import *
from collections import deque
import feedparser


@for_all_methods(logger.catch)
class RSSProvider(GenericProvider):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        super(RSSProvider, self).__init__(queue, config, id_list)

    def get_new_entries(self):
        feed = feedparser.parse(self.config['url'], agent=self.config['user_agent'])
        entries = {}
        entries_ids = []
        for entry in feed.entries:
            id_ = sha1sum(f"{self.__class__.__name__}{entry.link}")
            if self.id_list.is_id_present(id_):
                continue
            entries[id_] = {
                'link': entry.link,
                'title': entry.title
            }
            entries_ids.append(id_)

        return entries_ids, entries
