import asyncio
import logging
import os
import sys

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.bot import log
from telegram.ext import CommandHandler, CallbackContext, Updater, \
    MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

logging.basicConfig(level=logging.INFO,
                    format='%(filename)s: '
                           '%(levelname)s: '
                           '%(funcName)s(): '
                           '%(lineno)d:\t'
                           '%(message)s')

from config import token, PINGER_ENABLED

if PINGER_ENABLED:
    from bot_pinger import run_pinger


# hack for tornado ioloop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

toplevel_buttons = {
    "make_wish": "Загадать желание\N{Shooting Star}",
    "fulfill_wish": "Исполнить желание",
    "fulfilled_list": "Список исполненных",
    "todo": "Взято к выполнению"
}


def get_toplevel_markup():
    return ReplyKeyboardMarkup(
        [[toplevel_buttons['make_wish'], toplevel_buttons['fulfill_wish']],
         [toplevel_buttons['fulfilled_list'], toplevel_buttons['todo']],
         [KeyboardButton("Спросить номер", request_contact=True)]]
    )


@log
def start_callback(update: Update, _: CallbackContext):
    start_msg = '''Привет! Давай познакомимся😉\n
Нажми на кнопку внизу, чтобы отправить мне свой номер телефона'''
    update.message.reply_text(start_msg,
                              reply_markup=ReplyKeyboardMarkup(
                                  [[KeyboardButton("\N{Mobile Phone}", request_contact=True)]]
                              ))


def main():
    logging.info("Application started")
    updater = Updater(token, use_context=True)
    setup_handlers(updater)

    updater.start_polling()

    if PINGER_ENABLED:
        asyncio.run(run_pinger())
    else:
        updater.idle()
    if updater.running:
        updater.stop()
    logging.info("Application shut down")


def setup_handlers(updater):
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start_callback))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
