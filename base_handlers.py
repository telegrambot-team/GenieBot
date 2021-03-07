import logging
from functools import wraps

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.bot import log
from telegram.ext import CallbackContext

from config import ADMIN_IDS, ARTHUR_ID
from constants import start_msg, request_contact_text, default_handler_text, intro_msg, ADMIN_ALL_WISHES, \
    admin_buttons, toplevel_buttons, WISHES_IN_PROGRESS, MY_WISHES, FULFILLED_LIST, SELECT_WISH, MAKE_WISH


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
def default_handler(update: Update, ctx: CallbackContext):
    if 'contact' not in ctx.user_data:
        start_handler(update, ctx)
        return
    update.message.reply_text(default_handler_text,
                              reply_markup=get_toplevel_markup(update.effective_user.id))


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


def ups_handler(update, context):
    chat_id = update.effective_chat.id or ""
    logging.exception(context.error)
    msg_admin(context.bot, f'Following error occurred:\n'
                           f'{chat_id}\n'
                           f'{type(context.error)=}\n'
                           f'msg={context.error}')


@log
def contact_handler(update: Update, ctx: CallbackContext):
    logging.info(update)
    contact = update.message.contact
    phone = contact.phone_number
    if phone[0] == '7':
        phone = f'+{phone}'
    ctx.user_data['contact'] = (contact.first_name, phone)
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
