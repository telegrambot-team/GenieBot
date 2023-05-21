import asyncio
import logging
from functools import wraps

from pyrogram import Client

from telegram import Update, ReplyKeyboardMarkup
from telegram.bot import log
from telegram.ext import CallbackContext

from src.constants import (
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
    REMOVED, ARTHUR_STATISTICS,
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
def start_handler(update: Update, ctx: CallbackContext):
    # update.message.reply_text(
    #     start_msg,
    #     reply_markup=ReplyKeyboardMarkup(
    #         [[KeyboardButton(request_contact_text, request_contact=True)]],
    #         resize_keyboard=True,
    #     ),
    # )
    user = update.message.from_user
    if not user.username:
        update.message.reply_text("Для работы бота необходимо задать юзернейм. "
                                  "Он будет использоваться для связи между тобой и исполнителем твоего желания.\n"
                                  "Нажми ещё раз на /start когда добавишь юзернейм!")
        return
    if "wishes" not in ctx.user_data:
        ctx.user_data["wishes"] = {"created": [], "in_progress": [], "done": []}
    if "contact" not in ctx.user_data:
        ctx.user_data["contact"] = f"{user.full_name} @{user.username}"
    main_handler(update, ctx)


@log
def default_handler(update: Update, ctx: CallbackContext):
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
        xs.append([admin_buttons[ARTHUR_STATISTICS]])
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


@log
def get_chat_id(update: Update, ctx: CallbackContext):
    ctx.bot.send_message(99988303, str(update.message.chat_id))


@log
def list_move_chat(update: Update, ctx: CallbackContext):
    try:
        asyncio.get_event_loop()
    except RuntimeError as e:
        if str(e).startswith('There is no current event loop in thread'):
            logging.warning("Resetting event loop")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        else:
            raise

    bot_token = ctx.bot_data.config.bot_token
    api_id = ctx.bot_data.config.api_id
    api_hash = ctx.bot_data.config.api_hash
    with Client("my_account", api_id, api_hash, bot_token=bot_token) as app:
        mems = app.get_chat_members(-1001756263090)
        xs = []
        # noinspection PyTypeChecker
        for m in mems:
            name = m.user.first_name
            if m.user.last_name:
                name += " " + m.user.last_name
            if m.user.username:
                name += " @" + m.user.username
            xs.append(name)

    update.message.reply_text("\n".join(xs))


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


def main_handler(update: Update, ctx: CallbackContext):
    is_arthur = ctx.bot_data.config.arthur_id == update.effective_user.id
    update.message.reply_text(intro_msg, reply_markup=get_toplevel_markup(is_arthur))
