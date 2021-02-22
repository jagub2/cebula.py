from collections import deque
from bots import *
from cebula_common import IdList
from loguru import logger
import sys
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


@logger.catch
def main():
    queue = deque()

    with open('config.yaml', 'r') as f:
        yml = yaml.load(f, Loader=Loader)

    id_list = IdList(yml['global']['redis'])

    messenger_class = MessengerBot.MessengerThread(yml['global']['notifier']['class'], queue,
                                                   **yml['global']['notifier']['opts'])
    messenger_class.start()

    bots = {}
    for specific_name, specific_config in yml.items():
        if specific_name == 'global':
            continue
        config = yml['global'].copy()
        config.update(specific_config)
        bot_class, bot_name = specific_name.split('@')
        bots[bot_name] = ProviderBot.ProviderBot(queue, bot_class, config, id_list)

    for bot_instance in bots.values():
        ProviderBot.ProviderThread(bot_instance).start()


if __name__ == "__main__":
    main()
