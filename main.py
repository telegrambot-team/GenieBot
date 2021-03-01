import logging
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.bot import log
from telegram.ext import CommandHandler, CallbackContext, Updater, \
    MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

logging.basicConfig(level=logging.DEBUG,
                    format='%(filename)s: '
                           '%(levelname)s: '
                           '%(funcName)s(): '
                           '%(lineno)d:\t'
                           '%(message)s')

toplevel_buttons = {
    "make_wish": "Загадать желание\N{Shooting Star}",
    "fulfill_wish": "Исполнить желание",
    "fulfilled_list": "Список исполненных",
    "todo": "Взято к выполнению"
}

token = os.environ['BOT_TOKEN']


def get_toplevel_markup():
    return ReplyKeyboardMarkup(
        [[toplevel_buttons['make_wish'], toplevel_buttons['fulfill_wish']],
         [toplevel_buttons['fulfilled_list'], toplevel_buttons['todo']]]
    )

@log
def start_callback(update: Update, _: CallbackContext):
    hello_msg = '''Добро пожаловать в пещеру Джина!🧞‍♀️\n
    Тут можно оставить своё желание\n
    или исполнить чужое!'''
    update.message.reply_text(hello_msg,
                              reply_markup=get_toplevel_markup())
    logging.info("Update: %s", update)


def main():
    updater = Updater(token, use_context=True)
    setup_handlers(updater)

    updater.start_polling()


def setup_handlers(updater):
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start_callback))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
