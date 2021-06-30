import logging
from functools import wraps

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.bot import log
from telegram.ext import CallbackContext

from src.constants import (
    start_msg,
    request_contact_text,
    default_handler_text,
    intro_msg,
    ARTHUR_ALL_WISHES,
    admin_buttons,
    toplevel_buttons,
    WISHES_IN_PROGRESS,
    MY_WISHES,
    FULFILLED_LIST,
    SELECT_WISH,
    MAKE_WISH,
    REMOVED,
)


def restricted(func, admin_ids: list[int]):
    @wraps(func)
    def wrapped(update, context: CallbackContext, *args, **kwargs) -> None:
        user_id = update.effective_user.id
        if user_id not in admin_ids:
            text = f"Unauthorized access denied for {user_id}"
            logging.warning(text)
            msg_admin(context.bot_data.config.admin_ids, context.bot, text)
            return
        func(update, context, *args, **kwargs)

    return wrapped


@log
def start_handler(update: Update, _: CallbackContext):
    update.message.reply_text(
        start_msg,
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton(request_contact_text, request_contact=True)]],
            resize_keyboard=True,
        ),
    )


@log
def default_handler(update: Update, ctx: CallbackContext):
    if "contact" not in ctx.user_data:
        start_handler(update, ctx)
        return
    is_arthur = ctx.bot_data.config.arthur_id == update.effective_user.id
    update.message.reply_text(
        default_handler_text, reply_markup=get_toplevel_markup(is_arthur)
    )


def get_toplevel_markup(is_arthur):
    xs = [
        [toplevel_buttons[MAKE_WISH], toplevel_buttons[SELECT_WISH]],
        [
            toplevel_buttons[FULFILLED_LIST],
            toplevel_buttons[MY_WISHES],
            toplevel_buttons[WISHES_IN_PROGRESS],
        ],
    ]
    if is_arthur:
        xs.append([admin_buttons[ARTHUR_ALL_WISHES]])
    return ReplyKeyboardMarkup(xs, resize_keyboard=True)


def msg_admin(admin_ids, bot, message, **kwargs):
    for admin_id in admin_ids:
        bot.send_message(chat_id=admin_id, text=message, **kwargs)


@log
def drop_wish(update: Update, ctx: CallbackContext):
    # TODO: fix this, doesn't work
    chat_to_delete, wish_to_delete = map(int, ctx.args[0].split(":"))
    user_data = ctx.dispatcher.user_data.get(chat_to_delete)
    if (
        "wishes" not in user_data
        or len(user_data["wishes"]["created"]) < wish_to_delete
    ):
        update.message.reply_text("Неверные параметры")
        return
    wish_id = user_data["wishes"]["created"][wish_to_delete]
    wish = ctx.bot_data.wishes[str(wish_id)]
    # TODO: add other statuses
    if "fulfiller_id" in wish:
        fulfiller_data = ctx.dispatcher.user_data.get(wish["fulfiller_id"])
        if wish_id in fulfiller_data["wishes"]["in_progress"]:
            fulfiller_data["wishes"]["in_progress"].remove(wish_id)
            logging.info(fulfiller_data["wishes"]["in_progress"])
    wish["status"] = REMOVED

    del user_data["wishes"]["created"][wish_to_delete]
    update.message.reply_text("Желание удалено")


def ups_handler(update, context):
    chat_id = update.effective_chat.id or ""
    logging.exception(context.error)
    msg_admin(
        context.bot_data.config.admin_ids,
        context.bot,
        f"Following error occurred:\n"
        f"{chat_id}\n"
        f"{type(context.error)=}\n"
        f"msg={context.error}",
    )


@log
def contact_handler(update: Update, ctx: CallbackContext):
    logging.info(update)
    contact = update.message.contact
    phone = contact.phone_number
    if phone[0] != "+":
        phone = f"+{phone}"
    ctx.user_data["contact"] = (contact.first_name, phone)
    if "wishes" not in ctx.user_data:
        ctx.user_data["wishes"] = {"created": [], "in_progress": [], "done": []}
    main_handler(update, ctx)


def main_handler(update: Update, ctx: CallbackContext):
    is_arthur = ctx.bot_data.config.arthur_id == update.effective_user.id
    update.message.reply_text(intro_msg, reply_markup=get_toplevel_markup(is_arthur))
