import logging
import asyncio
import sys

from src.handlers_setup import setup_handlers
from telegram.ext import Updater

from src.config import get_config
from src.db_persistence import DBPersistence

# hack for tornado ioloop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def create_bot(conf):
    if conf.db_url:
        persistence = DBPersistence(conf.db_url)
        logging.info("Persistence enabled")
    else:
        persistence = None
        logging.warning("Persistence disabled")
    updater = Updater(conf.bot_token, use_context=True, persistence=persistence)
    setup_handlers(updater)
    return updater


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(filename)s: '
                               '%(levelname)s: '
                               '%(funcName)s(): '
                               '%(lineno)d:\t'
                               '%(message)s')
    logging.info("Application started")
    conf = get_config()
    updater = create_bot(conf)
    updater.start_polling()

    if conf.pinger_enabled:
        from bot_pinger import run_pinger
        asyncio.run(run_pinger())
    else:
        updater.idle()
    if updater.running:
        updater.stop()
    logging.info("Application shut down")


if __name__ == '__main__':
    main()
