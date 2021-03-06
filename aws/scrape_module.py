import json
from loguru import logger
from AllegroScraper import AllegroScraper

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/86.0'

def lambda_handler(event, context):
    url = None
    if 'queryStringParameters' in event and 'url' in event['queryStringParameters']:
        url = event['queryStringParameters']['url']
    else:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": "{}"
        }

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

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(entries)
    }
