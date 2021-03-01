import logging
import os

from dotenv import load_dotenv

load_dotenv()


token = os.environ['BOT_TOKEN']

PINGER_ENABLED = True

try:
    api_id = int(os.environ['PINGER_API_ID'])
    api_hash = os.environ['PINGER_API_HASH']
    BOT_LIST = os.environ['PINGER_BOT_LIST'].split(';')
    ADMIN_IDS = list(map(int, os.environ['ADMIN_IDS'].split(';')))
    DATABASE_URL = os.environ['DATABASE_URL']
    MSG_TIMEOUT = os.environ.get('MSG_TIMEOUT', 15)
    PINGER_SLEEP_TIME = os.environ.get('PINGER_SLEEP_TIME', 10)
except KeyError as e:
    logging.info(str(e))
    logging.info('Disabling pinger')
    PINGER_ENABLED = False
