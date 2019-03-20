from providers.GenericProvider import GenericProvider
import feedparser
import hashlib


class RSSProvider(GenericProvider):

    def __init__(self, config: dict, default_config: dict):
        super(RSSProvider, self).__init__(config, default_config)

    def get_new_entries(self):
        feed = feedparser.parse(self.config['url'], agent=self.config['user_agent'])
        entries = {}
        for entry in feed.entries:
            id_ = hashlib.sha1((self.config['url'] + entry.link).encode('utf-8')).hexdigest()
            entries[id_] = {
                'link': entry.link,
                'title': entry.title
            }

        new_entries_id = list(set(entries.keys()) - set(self.data.keys()))
        return new_entries_id, entries
