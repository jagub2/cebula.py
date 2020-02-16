from providers.GenericProvider import *
from cebula_common import *
from collections import deque
import feedparser


class RSSProvider(GenericProvider):

    def __init__(self, queue: deque, config: dict, id_list: IdList):
        super(RSSProvider, self).__init__(queue, config, id_list)

    def get_new_entries(self):
        feed = feedparser.parse(self.config['url'], agent=self.config['user_agent'])
        entries = {}
        entries_ids = []
        for entry in feed.entries:
            id_ = sha1sum(f"{self.__class__.__name__}{entry.link}")
            entries[id_] = {
                'link': entry.link,
                'title': entry.title
            }
            entries_ids.append(id_)

        new_entries_id = [entry for entry in entries_ids if not self.id_list.is_id_present(entry)]
        return new_entries_id, entries
