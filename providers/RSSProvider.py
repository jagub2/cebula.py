from providers.GenericProvider import GenericProvider
from queue import Queue
import feedparser
import hashlib


class RSSProvider(GenericProvider):

    def __init__(self, queue: Queue, config: dict):
        super(RSSProvider, self).__init__(queue, config)

    def get_new_entries(self):
        feed = feedparser.parse(self.config['url'], agent=self.config['user_agent'])
        entries = {}
        entries_ids = []
        for entry in feed.entries:
            id_ = hashlib.sha1(f"{self.config['url']}{entry.link}".encode('utf-8')).hexdigest()
            entries[id_] = {
                'link': entry.link,
                'title': entry.title
            }
            entries_ids.append(id_)

        new_entries_id = [entry for entry in entries_ids if entry not in self.data.keys()]
        return new_entries_id, entries
