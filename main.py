import logging

logging.basicConfig(level=logging.INFO,
                    format='%(filename)s: '
                           '%(levelname)s: '
                           '%(funcName)s(): '
                           '%(lineno)d:\t'
                           '%(message)s')

from config import token, PINGER_ENABLED, DATABASE_URL, ADMIN_IDS, ARTHUR_ID
import asyncio
import sys
from functools import wraps

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.bot import log
from telegram.ext import CommandHandler, CallbackContext, Updater, \
    MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

from button_handlers import button_handler, make_wish_handler, incorrect_wish_handler, fulfill_wish_handler, \
    remove_wish_handler, take_wish_handler, proof_handler
from postgres_persistence import PostgresPersistence
from constants import intro_msg, start_msg, toplevel_buttons, request_contact_text, default_handler_text, \
    error_text, WAITING_FOR_PROOF, MAKE_WISH, SELECT_WISH, FULFILLED_LIST, MY_WISHES, \
    WISHES_IN_PROGRESS, take_wish_inline_btn, drop_wish_inline_btn, fulfill_wish_inline_btn, admin_buttons, \
    ADMIN_ALL_WISHES

if PINGER_ENABLED:
    from bot_pinger import run_pinger

# hack for tornado ioloop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_toplevel_markup(user_id):
    xs = [[toplevel_buttons[MAKE_WISH],
          toplevel_buttons[SELECT_WISH]],
         [toplevel_buttons[FULFILLED_LIST],
          toplevel_buttons[MY_WISHES],
          toplevel_buttons[WISHES_IN_PROGRESS]]]
    if user_id == ARTHUR_ID:
        xs.append([
            admin_buttons[ADMIN_ALL_WISHES]
        ])
    return ReplyKeyboardMarkup(xs, resize_keyboard=True)


def msg_admin(bot, message, **kwargs):
    for admin_id in ADMIN_IDS:
        bot.send_message(chat_id=admin_id, text=message, **kwargs)


def ups_handler(update, context):
    chat_id = update.effective_chat.id or ""
    logging.exception(context.error)
    msg_admin(context.bot, f'Following error occured:\n'
                           f'{chat_id}\n'
                           f'{type(context.error)=}\n'
                           f'msg={context.error}')


@log
def start_handler(update: Update, ctx: CallbackContext):
    if 'wishes' not in ctx.bot_data:
        ctx.bot_data['wishes'] = {}
    update.message.reply_text(start_msg,
                              reply_markup=ReplyKeyboardMarkup(
                                  [[KeyboardButton(
                                      request_contact_text, request_contact=True)]],
                                  resize_keyboard=True
                              ))


@log
def default_handler(update: Update, _: CallbackContext):
    update.message.reply_text(default_handler_text,
                              reply_markup=get_toplevel_markup(update.effective_user.id))


@log
def contact_handler(update: Update, ctx: CallbackContext):
    logging.info(update)
    contact = update.message.contact
    ctx.user_data['contact'] = (contact.first_name, contact.phone_number)
    if 'wishes' not in ctx.user_data:
        ctx.user_data['wishes'] = {
            'created': [],
            'in_progress': [],
            'done': []
        }
    main_handler(update, ctx)


def main_handler(update: Update, _: CallbackContext):
    update.message.reply_text(intro_msg,
                              reply_markup=get_toplevel_markup(update.effective_user.id))


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
    dispatcher.add_handler(
        CommandHandler("start", start_handler))
    dispatcher.add_handler(
        CommandHandler("dropwish", drop_wish))
    dispatcher.add_handler(
        MessageHandler(Filters.contact, contact_handler))
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[
                MessageHandler(Filters.text(list(toplevel_buttons.values())+
                                            list(admin_buttons.values())),
                               button_handler)
            ],
            states={
                MAKE_WISH:
                    [MessageHandler(Filters.text, make_wish_handler),
                     MessageHandler(Filters.chat_type.private, incorrect_wish_handler)]
            },
            fallbacks=[],
            persistent=True, name='ButtonsHandler', per_chat=False
        )
    )
    dispatcher.add_handler(CallbackQueryHandler(remove_wish_handler,
                                                pattern=f'^{drop_wish_inline_btn}.*'))
    dispatcher.add_handler(CallbackQueryHandler(take_wish_handler,
                                                pattern=f'^{take_wish_inline_btn}.*'))
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[
                CallbackQueryHandler(fulfill_wish_handler,
                                     pattern=f'^{fulfill_wish_inline_btn}.*')
            ],
            states={
                WAITING_FOR_PROOF:
                    [
                        MessageHandler(Filters.chat_type.private, proof_handler)
                    ]
            },
            fallbacks=[],
            persistent=True, name='ProofHandler', per_chat=False
        ))
    dispatcher.add_handler(MessageHandler(
        Filters.chat_type.private, default_handler))

    dispatcher.add_error_handler(ups_handler)


def restricted(func):
    @wraps(func)
    def wrapped(update, context: CallbackContext, *args, **kwargs) -> None:
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            text = f"Unauthorized access denied for {user_id}"
            logging.warning(text)
            msg_admin(context.bot, text)
            return
        func(update, context, *args, **kwargs)

    return wrapped


@log
@restricted
def drop_wish(update: Update, ctx: CallbackContext):
    chat_to_delete, wish_to_delete = map(int, ctx.args[0].split(":"))
    user_data = ctx.dispatcher.user_data.get(chat_to_delete)
    if 'wishes' not in user_data or len(user_data['wishes']) < wish_to_delete:
        update.message.reply_text("Неверные параметры")
        return
    del user_data['wishes']['created'][wish_to_delete]
    update.message.reply_text("Желание удалено")


if __name__ == '__main__':
    main()
