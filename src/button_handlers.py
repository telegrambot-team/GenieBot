import itertools
import logging
import math
from collections import Counter

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.bot import log
from telegram.ext import CallbackContext, ConversationHandler
from telegram.error import BadRequest

import src.constants
from src.base_handlers import start_handler, main_handler, get_toplevel_markup
import src.constants as constants


def incorrect_wish_handler(update: Update, _: CallbackContext):
    update.message.reply_text("Я только читать умею, ты текстом пиши")
    return constants.MAKE_WISH


def cancel_wish_making_handler(update: Update, ctx: CallbackContext):
    main_handler(update, ctx)
    return ConversationHandler.END


def make_wish_handler(update: Update, ctx: CallbackContext):
    wish_id = len(ctx.bot_data.wishes)
    new_wish = {
        "wish_id": wish_id,
        "creator_id": update.effective_user.id,
        "text": update.message.text,
        "fulfiller_id": None,
        "status": constants.WAITING,
        "proof_msg_id": None,
    }
    # str is used because of storing dict as json; json can not have int keys
    ctx.bot_data.wishes[str(wish_id)] = new_wish
    ctx.user_data["wishes"]["created"].append(wish_id)

    is_arthur = ctx.bot_data.config.arthur_id == update.effective_user.id
    update.message.reply_text(
        constants.lock_and_load, reply_markup=get_toplevel_markup(is_arthur)
    )
    return ConversationHandler.END


def list_my_wishes(update: Update, ctx: CallbackContext):
    if not ctx.user_data["wishes"]["created"]:
        update.message.reply_text(constants.no_self_created_wishes)
        return

    ctx.user_data["list_wish_msg_id"] = {}

    for wish_id in ctx.user_data["wishes"]["created"]:
        wish = ctx.bot_data.wishes[str(wish_id)]
        if wish["status"] == constants.WAITING:
            kbd = InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    constants.delete_wish_btn_txt,
                    callback_data=f"{constants.drop_wish_inline_btn} {wish_id}",
                )
            )
        elif wish["status"] == constants.IN_PROGRESS:
            kbd = InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    "Выполняется" "\N{Hourglass with Flowing Sand}",
                    callback_data="pass",
                )
            )
        elif wish["status"] == constants.DONE:
            kbd = InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    "Выполнено" "\N{White Heavy Check Mark}", callback_data="pass"
                )
            )
        else:
            raise RuntimeError(f"Invalid wish status {wish['status']}")
        msg = update.message.reply_text(wish["text"], reply_markup=kbd)
        ctx.user_data["list_wish_msg_id"][wish_id] = msg.message_id
    return ConversationHandler.END


@log
def remove_wish_handler(update: Update, ctx: CallbackContext):
    wish_id = int(update.callback_query.data.split(" ")[1])
    chat_id = update.effective_chat.id
    msg_id = ctx.user_data["list_wish_msg_id"][wish_id]
    ctx.bot.delete_message(chat_id, msg_id)

    ctx.user_data["wishes"]["created"].remove(wish_id)
    wish = ctx.bot_data.wishes[str(wish_id)]
    if wish["status"] == constants.IN_PROGRESS:
        fulfiller_data = ctx.dispatcher.user_data.get(wish["fulfiller_id"])
        fulfiller_data["wishes"]["in_progress"].remove(wish_id)
    wish["status"] = constants.REMOVED


def is_last_wish(idx, slice_start_idx, total_len, wish_group_limit):
    return slice_start_idx + idx + 1 == total_len or idx + 1 == wish_group_limit


def render_wishes(update: Update, ctx: CallbackContext):
    counter = 0
    chat_id = update.effective_chat.id
    start_idx = ctx.user_data["start_idx"]
    ctx.user_data["select_wish_msg_id"] = []
    end_idx = start_idx + constants.WISHES_TO_SHOW_LIMIT

    reversed_wishes = reversed(ctx.bot_data.wishes.values())

    def wish_filter(wish_):
        if wish_["creator_id"] == chat_id or wish_["status"] != constants.WAITING:
            return False
        return True

    filtered_wishes = list(filter(wish_filter, reversed_wishes))
    wishes_slice = list(itertools.islice(filtered_wishes, start_idx, end_idx))
    enable_paging = len(filtered_wishes) > constants.WISHES_TO_SHOW_LIMIT
    ctx.user_data["len_filtered_wishes"] = len(filtered_wishes)
    group_count = math.ceil(len(filtered_wishes) / constants.WISHES_TO_SHOW_LIMIT)
    page_number = start_idx // constants.WISHES_TO_SHOW_LIMIT + 1
    for idx, wish in enumerate(wishes_slice):
        btn_multilist = [
            [
                InlineKeyboardButton(
                    "Взять",
                    callback_data=f"{constants.take_wish_inline_btn} {wish['wish_id']}",
                )
            ]
        ]
        last_wish = is_last_wish(
            idx, start_idx, len(filtered_wishes), constants.WISHES_TO_SHOW_LIMIT
        )
        if enable_paging and last_wish:
            btn_multilist.append(
                [
                    InlineKeyboardButton(
                        "\N{LEFTWARDS BLACK ARROW}",
                        callback_data=f"{constants.take_wish_inline_btn} left",
                    ),
                    InlineKeyboardButton(
                        f"{page_number} из {group_count}", callback_data="ignore"
                    ),
                    InlineKeyboardButton(
                        "\N{BLACK RIGHTWARDS ARROW}",
                        callback_data=f"{constants.take_wish_inline_btn} right",
                    ),
                ]
            )
        kbd = InlineKeyboardMarkup(btn_multilist)
        msg = ctx.bot.send_message(
            chat_id, wish["text"], reply_markup=kbd, disable_notification=True
        )
        ctx.user_data["select_wish_msg_id"].append(msg.message_id)
        counter += 1

    if counter == 0:
        ctx.bot.send_message(chat_id, "Пока нет желаний для выполнения")


@log
def select_wish(update: Update, ctx: CallbackContext):
    chat_id = update.effective_chat.id
    if len(ctx.user_data["wishes"]["in_progress"]) >= 3:
        ctx.bot.send_message(chat_id, src.constants.wish_limit_str)
        return

    ctx.user_data["start_idx"] = 0
    ctx.user_data['selecting_wish'] = 1
    render_wishes(update, ctx)


@log
def control_list_wish_handler(update: Update, ctx: CallbackContext):
    chat_id = update.effective_chat.id

    if ctx.user_data['selecting_wish'] == 0:
        logging.warning(f"Ignoring duplicate call of control_list_wish_handler with user_data={ctx.user_data}")
        return

    wish_data = update.callback_query.data.split(" ")[1]
    if wish_data == "right":
        new_idx = ctx.user_data["start_idx"] + constants.WISHES_TO_SHOW_LIMIT
    elif wish_data == "left":
        new_idx = ctx.user_data["start_idx"] - constants.WISHES_TO_SHOW_LIMIT
    else:
        raise RuntimeError("Unexpected command")
    if new_idx < 0 or ctx.user_data["len_filtered_wishes"] <= new_idx:
        return
    ctx.user_data["start_idx"] = new_idx

    safe_delete_msg_list(ctx.user_data["select_wish_msg_id"], chat_id, ctx.bot)

    render_wishes(update, ctx)


@log
def take_wish_handler(update: Update, ctx: CallbackContext):
    if ctx.user_data['selecting_wish'] == 0:
        logging.warning(f"Ignoring duplicate call of take_wish_handler with user_data={ctx.user_data}")
        return
    wish_data = update.callback_query.data.split(" ")[1]
    wish_id = int(wish_data)
    chat_id = update.effective_chat.id

    safe_delete_msg_list(ctx.user_data["select_wish_msg_id"], chat_id, ctx.bot)

    del ctx.user_data["start_idx"]
    del ctx.user_data["select_wish_msg_id"]
    ctx.user_data['selecting_wish'] = 0

    wish = ctx.bot_data.wishes[str(wish_id)]
    if wish['status'] != constants.WAITING:
        ctx.bot.send_message(chat_id, "Это желание уже взяли😅")
        return
    wish["status"] = constants.IN_PROGRESS
    wish["fulfiller_id"] = chat_id

    ctx.user_data["wishes"]["in_progress"].append(wish_id)

    creator_data = ctx.dispatcher.user_data.get(wish["creator_id"])
    creator_name = creator_data["contact"]

    text = constants.wish_taken.format(
        wish_text=wish["text"], creator_name=creator_name
    )
    ctx.bot.send_message(chat_id, text)
    ctx.bot.send_message(wish["creator_id"], constants.magick_begins)


@log
def list_fulfilled(update: Update, ctx: CallbackContext):
    if not ctx.user_data["wishes"]["done"]:
        update.message.reply_text(constants.no_self_wishes)
        return
    for wish_id in ctx.user_data["wishes"]["done"]:
        wish_text = ctx.bot_data.wishes[str(wish_id)]["text"]
        creator_data = ctx.dispatcher.user_data.get(
            ctx.bot_data.wishes[str(wish_id)]["creator_id"]
        )
        creator_name = creator_data["contact"]
        msg_text = f"{wish_text}\n{creator_name}"
        update.message.reply_text(msg_text, disable_notification=True)


@log
def list_in_progress(update: Update, ctx: CallbackContext):
    if not ctx.user_data["wishes"]["in_progress"]:
        update.message.reply_text("Вы ещё не взяли на себя ни одного желания")
        return

    ctx.user_data["fulfill_wish_msg_id"] = []
    for wish_id in ctx.user_data["wishes"]["in_progress"]:
        wish = ctx.bot_data.wishes[str(wish_id)]
        assert wish["status"] == constants.IN_PROGRESS
        kbd = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                "Отправить фото или видео",
                callback_data=f"{constants.fulfill_wish_inline_btn} {wish_id}",
            )
        )
        creator_data = ctx.dispatcher.user_data.get(wish["creator_id"])
        creator_name = creator_data["contact"]

        msg_text = f"{wish['text']}\n{creator_name}"
        msg = update.message.reply_text(
            msg_text, reply_markup=kbd, disable_notification=True
        )
        ctx.user_data["fulfill_wish_msg_id"].append(msg.message_id)


def safe_delete_msg_list(msg_ids, chat_id, bot):
    try:
        for msg_id in msg_ids:
            bot.delete_message(chat_id, msg_id)
    except BadRequest as e:
        if e.message != "Message can't be deleted for everyone":
            raise

        logging.warning(e)


@log
def fulfill_wish_handler(update: Update, ctx: CallbackContext):
    wish_id = int(update.callback_query.data.split(" ")[1])
    chat_id = update.effective_chat.id

    safe_delete_msg_list(ctx.user_data["fulfill_wish_msg_id"], chat_id, ctx.bot)

    ctx.bot.send_message(
        chat_id,
        "\N{Genie}Жду подтверждение выполненного желания.\n"
        "Отправь фото или видео\N{Winking Face}",
        reply_markup=get_cancel_markup(),
    )
    ctx.user_data["wish_waiting_for_proof"] = wish_id

    return constants.WAITING_FOR_PROOF


@log
def proof_handler(update: Update, ctx: CallbackContext):
    if update.message.text and update.message.text == constants.cancel_wish_taking:
        main_handler(update, ctx)
        return ConversationHandler.END
    if not update.message.photo and not update.message.video:
        update.message.reply_text("Отправьте фото или видео")
        return constants.WAITING_FOR_PROOF
    wish_id = ctx.user_data["wish_waiting_for_proof"]
    wish = ctx.bot_data.wishes[str(wish_id)]
    wish["status"] = constants.DONE
    wish["proof_msg_id"] = update.message.message_id
    ctx.user_data["wishes"]["done"].append(wish_id)
    ctx.user_data["wishes"]["in_progress"].remove(wish_id)
    is_arthur = ctx.bot_data.config.arthur_id == update.effective_user.id
    update.message.reply_text(
        "Желание исполнено👍", reply_markup=get_toplevel_markup(is_arthur)
    )

    creator_id = wish["creator_id"]
    ctx.bot.forward_message(creator_id, wish["fulfiller_id"], wish["proof_msg_id"])
    ctx.bot.send_message(creator_id, "Желание исполнено👍")
    return ConversationHandler.END


@log
def admin_list_all_wishes(update: Update, ctx: CallbackContext):
    conf = ctx.bot_data.config
    for wish in ctx.bot_data.wishes.values():
        if wish["status"] != constants.DONE:
            continue

        creator_data = ctx.dispatcher.user_data.get(wish["creator_id"])
        creator_name = creator_data["contact"]

        msg_text = f"{wish['text']}\n{creator_name}"
        update.message.reply_text(msg_text)
        try:
            ctx.bot.forward_message(
                conf.arthur_id, wish["fulfiller_id"], wish["proof_msg_id"]
            )
        except BadRequest as e:
            logging.warning("Missing msg:", e)


def get_cancel_markup():
    xs = [[constants.cancel_wish_making]]
    return ReplyKeyboardMarkup(xs, resize_keyboard=True)


def admin_list_statistics(update: Update, ctx: CallbackContext):
    fulfilled_wishes = list(filter(lambda w: w['status'] == constants.DONE, ctx.bot_data.wishes.values()))

    top_creators = Counter([w['creator_id'] for w in fulfilled_wishes])
    top_fulfillers = Counter([w['fulfiller_id'] for w in fulfilled_wishes])

    update.message.reply_text(f"Людей в боте: {len(ctx.dispatcher.user_data)}\n"
                              f"Желаний загадано: {len(ctx.bot_data.wishes)}\n"
                              f"Желаний исполнено: {len(fulfilled_wishes)}")

    best_creators_msg = "Чьи желания были самыми выполняемыми:\n"
    for telegram_id, wish_count in top_creators.most_common(3):
        assert telegram_id in ctx.dispatcher.user_data
        contact = ctx.dispatcher.user_data[telegram_id]["contact"]
        best_creators_msg += f"{contact} — {wish_count}\n"

    update.message.reply_text(best_creators_msg)

    best_fulfillers_msg = "Кто больше всех выполнял:\n"
    for telegram_id, wish_count in top_fulfillers.most_common(3):
        assert telegram_id in ctx.dispatcher.user_data
        contact = ctx.dispatcher.user_data[telegram_id]["contact"]
        best_fulfillers_msg += f"{contact} — {wish_count}\n"

    update.message.reply_text(best_fulfillers_msg)


@log
def button_handler(update: Update, ctx: CallbackContext):
    if "contact" not in ctx.user_data:
        start_handler(update, ctx)
        return
    text = update.message.text
    if text == constants.toplevel_buttons[constants.MAKE_WISH]:
        update.message.reply_text(
            constants.waiting_for_wish, reply_markup=get_cancel_markup()
        )
        return constants.MAKE_WISH
    elif text == constants.toplevel_buttons[constants.SELECT_WISH]:
        select_wish(update, ctx)
        return ConversationHandler.END
    elif text == constants.toplevel_buttons[constants.FULFILLED_LIST]:
        list_fulfilled(update, ctx)
        return ConversationHandler.END
    elif text == constants.toplevel_buttons[constants.WISHES_IN_PROGRESS]:
        list_in_progress(update, ctx)
        return ConversationHandler.END
    elif text == constants.toplevel_buttons[constants.MY_WISHES]:
        list_my_wishes(update, ctx)
        return ConversationHandler.END
    elif text == constants.admin_buttons[constants.ARTHUR_ALL_WISHES]:
        assert update.effective_user.id == ctx.bot_data.config.arthur_id
        admin_list_all_wishes(update, ctx)
        return ConversationHandler.END

    elif text == constants.admin_buttons[constants.ARTHUR_STATISTICS]:
        assert update.effective_user.id == ctx.bot_data.config.arthur_id
        admin_list_statistics(update, ctx)
        return ConversationHandler.END
