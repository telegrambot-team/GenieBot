import logging
import asyncio
import sys

from handlers_setup import setup_handlers
from telegram.ext import Updater

from postgres_persistence import PostgresPersistence

logging.basicConfig(level=logging.INFO,
                    format='%(filename)s: '
                           '%(levelname)s: '
                           '%(funcName)s(): '
                           '%(lineno)d:\t'
                           '%(message)s')

from config import token, PINGER_ENABLED, DATABASE_URL

if PINGER_ENABLED:
    from bot_pinger import run_pinger

# hack for tornado ioloop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def main():
    logging.info("Application started")
    persistence = PostgresPersistence(DATABASE_URL)
    updater = Updater(token, use_context=True, persistence=persistence)
    setup_handlers(updater)

    updater.start_polling()

    if PINGER_ENABLED:
        asyncio.run(run_pinger())
    else:
        updater.idle()
    if updater.running:
        updater.stop()
    logging.info("Application shut down")


if __name__ == '__main__':
    main()
