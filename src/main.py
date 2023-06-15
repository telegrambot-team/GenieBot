import logging
import asyncio
import sys

from telegram import Update
from telegram.ext.contexttypes import ContextTypes

from src.handlers_setup import setup_handlers
from telegram.ext import Updater

from src.config import get_config, BotData
from src.db_persistence import DBPersistence

# hack for tornado ioloop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def create_bot(conf):
    if conf.db_url:
        persistence = DBPersistence(conf.db_url)
        logging.info("Persistence enabled")
    else:
        persistence = None
        logging.warning("Persistence disabled")
    context_types = ContextTypes(bot_data=BotData)
    updater = Updater(
        conf.bot_token,
        use_context=True,
        persistence=persistence,
        context_types=context_types,
    )
    setup_handlers(updater, conf.admin_ids)
    updater.dispatcher.bot_data.config = conf
    updater.dispatcher.update_persistence()
    return updater


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s: "
               "%(filename)s: "
               "%(levelname)s: "
               "%(funcName)s(): "
               "%(lineno)d:\t"
               "%(message)s",
    )
    logging.info("Application started")
    conf = get_config()
    updater = create_bot(conf)
    updater.start_polling(allowed_updates=Update.ALL_TYPES)

    updater.idle()

    if updater.running:
        updater.stop()
    logging.info("Application shut down")


# TODO: logging every handler triggered by user
if __name__ == "__main__":
    main()
