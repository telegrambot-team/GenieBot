import asyncio
import logging
import os
import sys

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.bot import log
from telegram.ext import CommandHandler, CallbackContext, Updater, \
    MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

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

toplevel_buttons = {
    "make_wish": "Загадать желание\N{Shooting Star}",
    "fulfill_wish": "Исполнить желание",
    "fulfilled_list": "Список исполненных",
    "todo": "Взято к выполнению",
    "main": "Ко входу\N{Genie}"
}


def get_toplevel_markup():
    return ReplyKeyboardMarkup(
        [[toplevel_buttons['make_wish'], toplevel_buttons['fulfill_wish']],
         [toplevel_buttons['fulfilled_list'], toplevel_buttons['todo']]],
        resize_keyboard=True
    )


@log
def start_handler(update: Update, _: CallbackContext):
    start_msg = '''Привет! Давай познакомимся😉\n
Нажми на кнопку внизу, чтобы отправить мне свой номер телефона'''
    update.message.reply_text(start_msg,
                              reply_markup=ReplyKeyboardMarkup(
                                  [[KeyboardButton("Отправить\N{Mobile Phone}", request_contact=True)]],
                                  resize_keyboard=True
                              ))


@log
def contact_handler(update: Update, ctx: CallbackContext):
    logging.info(update)
    contact = update.message.contact
    ctx.user_data['contact'] = (contact.first_name, contact.phone_number)
    main_handler(update, ctx)


def main_handler(update: Update, _: CallbackContext):
    intro_msg = '''Добро пожаловать в пещеру Джина!\N{Genie}
Тут можно загадать своё желание
или исполнить чужое!'''
    update.message.reply_text(intro_msg,
                              reply_markup=get_toplevel_markup())


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


def setup_handlers(updater):
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start_handler))
    dispatcher.add_handler(MessageHandler(Filters.contact, contact_handler))


if __name__ == '__main__':
    main()
