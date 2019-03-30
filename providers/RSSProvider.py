from providers.GenericProvider import *
from cebula_common import *
from collections import deque
import feedparser


class RSSProvider(GenericProvider):

    def __init__(self, queue: deque, config: dict):
        super(RSSProvider, self).__init__(queue, config)

    def get_new_entries(self):
        feed = feedparser.parse(self.config['url'], agent=self.config['user_agent'])
        entries = {}
        entries_ids = []
        for entry in feed.entries:
            id_ = sha1sum(f"{self.config['url']}{entry.link}")
            entries[id_] = {
                'link': entry.link,
                'title': entry.title
            }
            entries_ids.append(id_)

        new_entries_id = [entry for entry in entries_ids if entry not in self.data.keys()]
        return new_entries_id, entries
