import json
from loguru import logger
from AllegroScraper import AllegroScraper

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/86.0'
ALLOWED_API_KEY = ''

def lambda_handler(event):
    url = None
    bad_response = json.dumps([])

    if event.args and 'url' in event.args:
        url = event.args['url']
    else:
        return bad_response

    if event.headers and 'X-API-Key' in event.headers:
        if event.headers['X-API-Key'] == ALLOWED_API_KEY:
            pass
        else:
            return bad_response
    else:
        return bad_response

    config = {
        'url': url,
        'user_agent': USER_AGENT,
        'include_promoted': True,
        'limit': 60
    }

    scraper = AllegroScraper(config)

    logger.info("Requesting Allegro data...")
    entries = scraper.get_entries()
    logger.info("Job done")

    return json.dumps(entries)

